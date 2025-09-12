data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
}

resource "aws_api_gateway_rest_api" "api" {
  name        = var.api_name
  description = length(var.api_description) > 1 ? var.api_description : null

  endpoint_configuration {
    types            = var.api_is_private ? ["PRIVATE"] : ["REGIONAL"]
    vpc_endpoint_ids = var.api_is_private ? ["${var.api_vpc_endpoint_id}"] : null
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = var.rest_api_tags
}

resource "aws_api_gateway_request_validator" "validator" {
  name                        = "${var.api_name}-validator"
  rest_api_id                = aws_api_gateway_rest_api.api.id
  validate_request_body      = true
  validate_request_parameters = true
}

data "aws_iam_policy_document" "api_resource_policy" {
  statement {
    effect    = "Allow"
    resources = ["arn:aws:execute-api:${var.region}:${local.account_id}:${aws_api_gateway_rest_api.api.id}/${var.stage_name}/*/*"]
    actions   = ["execute-api:Invoke"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${local.account_id}:root"]  # Restrict to your own account
    }
  }

  statement {
    effect    = "Deny"
    resources = ["arn:aws:execute-api:${var.region}:${local.account_id}:${aws_api_gateway_rest_api.api.id}/${var.stage_name}/*/*"]
    actions   = ["execute-api:Invoke"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    condition {
      test     = "NotIpAddress"
      variable = "aws:SourceIp"
      values   = var.allowlisted_ips
    }
  }

  depends_on = [aws_api_gateway_rest_api.api]
}

resource "aws_api_gateway_rest_api_policy" "resource_based_api" {
  count       = length(var.allowlisted_ips) > 0 ? 1 : 0
  rest_api_id = aws_api_gateway_rest_api.api.id
  policy      = data.aws_iam_policy_document.api_resource_policy.json
}

resource "aws_api_gateway_resource" "rest_resource" {
  for_each    = { for i, res in var.api_resources : i => res }
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = each.value.path_part
  depends_on  = [aws_api_gateway_rest_api.api]
}

resource "aws_api_gateway_method" "method" {
  for_each         = aws_api_gateway_resource.rest_resource
  rest_api_id      = each.value.rest_api_id
  resource_id      = each.value.id
  http_method      = var.api_resources[each.key].http_method
  authorization    = "NONE"
  api_key_required = false
  request_validator_id = aws_api_gateway_request_validator.validator.id
  request_parameters = {
    "method.request.header.Content-Type" = true
    "method.request.header.x-ms-conversation-id" = true
  }
  depends_on       = [aws_api_gateway_resource.rest_resource]
}

resource "aws_api_gateway_integration" "integration" {
  for_each                = aws_api_gateway_resource.rest_resource
  rest_api_id             = each.value.rest_api_id
  resource_id             = each.value.id
  http_method             = var.api_resources[each.key].http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  credentials             = length(var.api_resources[each.key].api_gateway_execution_role_arn) > 1 ? var.api_resources[each.key].api_gateway_execution_role_arn : null
  uri                     = length(var.api_resources[each.key].lambda_proxy_invoke_arn) > 0 ? var.api_resources[each.key].lambda_proxy_invoke_arn : "arn:aws:apigateway:${var.region}:lambda:path/2015-03-31/functions/${var.api_resources[each.key].lambda_proxy_arn}/invocations"
  depends_on              = [aws_api_gateway_method.method]
}

resource "aws_api_gateway_method_response" "response_200" {
  for_each    = aws_api_gateway_resource.rest_resource
  rest_api_id = each.value.rest_api_id
  resource_id = each.value.id
  http_method = var.api_resources[each.key].http_method
  status_code = "200"
  response_models = {
    "application/json" = "Empty"
  }
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
  depends_on = [aws_api_gateway_method.method, aws_api_gateway_integration.integration]
}

# ----------------------------------------------------------
#        Add Lambda function(s) persmission/trigger
# ----------------------------------------------------------
resource "aws_lambda_permission" "lambda_permission" {
  for_each      = aws_api_gateway_resource.rest_resource
  statement_id  = "Statement${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = var.api_resources[each.key].lambda_function_name
  principal     = "apigateway.amazonaws.com"

  # The /* part allows invocation from any stage, method and resource path
  # within API Gateway.
  source_arn = "${aws_api_gateway_rest_api.api.execution_arn}/*/${aws_api_gateway_method.method[each.key].http_method}/${aws_api_gateway_resource.rest_resource[each.key].path_part}"
  depends_on = [aws_api_gateway_rest_api.api, aws_api_gateway_resource.rest_resource, aws_api_gateway_method.method]
}

# ----------------------------------------------------------
#                          CORS
# ----------------------------------------------------------
resource "aws_api_gateway_method" "options_method" {
  for_each             = aws_api_gateway_resource.rest_resource
  rest_api_id          = each.value.rest_api_id
  resource_id          = each.value.id
  http_method          = "OPTIONS"
  authorization        = "NONE"
  api_key_required     = false
  request_validator_id = aws_api_gateway_request_validator.validator.id
  depends_on           = [aws_api_gateway_method.method, aws_api_gateway_integration.integration, aws_api_gateway_method_response.response_200]
}

resource "aws_api_gateway_integration" "options_integration" {
  for_each             = aws_api_gateway_resource.rest_resource
  rest_api_id          = each.value.rest_api_id
  resource_id          = each.value.id
  http_method          = aws_api_gateway_method.options_method[each.key].http_method
  type                 = "MOCK"
  passthrough_behavior = "WHEN_NO_MATCH"
  request_templates = {
    "application/json" : "{\"statusCode\": 200}"
  }
  depends_on = [aws_api_gateway_method.options_method]
}

resource "aws_api_gateway_method_response" "options_200" {
  for_each    = aws_api_gateway_resource.rest_resource
  rest_api_id = each.value.rest_api_id
  resource_id = each.value.id
  http_method = aws_api_gateway_integration.options_integration[each.key].http_method
  status_code = "200"
  response_models = {
    "application/json" = "Empty"
  }
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
  depends_on = [aws_api_gateway_method.options_method, aws_api_gateway_integration.options_integration]
}

resource "aws_api_gateway_integration_response" "options_integration_response" {
  for_each    = aws_api_gateway_resource.rest_resource
  rest_api_id = each.value.rest_api_id
  resource_id = each.value.id
  http_method = aws_api_gateway_integration.options_integration[each.key].http_method
  status_code = "200"
  response_parameters = {
    # "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Headers" = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'${var.api_resources[each.key].http_method},OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
  depends_on = [aws_api_gateway_method.options_method, aws_api_gateway_integration.options_integration, aws_api_gateway_method_response.options_200]
}

# ----------------------------------------------------------
#                      Deployment
# ----------------------------------------------------------
resource "aws_api_gateway_deployment" "deployment" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.rest_resource,
      aws_api_gateway_method.method,
      aws_api_gateway_integration.integration,
      data.aws_iam_policy_document.api_resource_policy,
      aws_api_gateway_rest_api_policy.resource_based_api
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
  depends_on = [aws_api_gateway_method_response.response_200, aws_api_gateway_integration_response.options_integration_response]
}

# ----------------------------------------------------------
#                         Stage
# ----------------------------------------------------------

resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.api.id}/${var.stage_name}"
  retention_in_days = var.cloudwatch_log_retention_days
  kms_key_id        = var.cloudwatch_encryption_key
}

resource "aws_api_gateway_stage" "stage" {
  deployment_id = aws_api_gateway_deployment.deployment.id
  rest_api_id   = aws_api_gateway_rest_api.api.id
  stage_name    = var.stage_name
  
  # Enable X-Ray tracing
  xray_tracing_enabled = true
  
  # Enable caching
  cache_cluster_enabled = true
  cache_cluster_size    = "0.5"
  
  # Enable access logging
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      integrationLatency = "$context.integrationLatency"
      responseLatency = "$context.responseLatency"
    })
  }

  tags = var.stage_tags

  depends_on = [aws_api_gateway_deployment.deployment, aws_cloudwatch_log_group.api_gateway_logs]
}

# ----------------------------------------------------------
#                        API key
# ----------------------------------------------------------
resource "aws_api_gateway_api_key" "api_key" {
  name       = "${var.api_name}-api-key"
  depends_on = [aws_api_gateway_stage.stage]
  tags       = var.api_key_tags
}

# ----------------------------------------------------------
#                       Usage plan
# ----------------------------------------------------------
resource "aws_api_gateway_usage_plan" "usage_plan" {
  name = "${var.api_name}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.api.id
    stage  = aws_api_gateway_stage.stage.stage_name
  }
  depends_on = [aws_api_gateway_stage.stage, aws_api_gateway_api_key.api_key]
  tags       = var.usage_plan_tags
}

resource "aws_api_gateway_usage_plan_key" "main" {
  key_id        = aws_api_gateway_api_key.api_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.usage_plan.id
  depends_on    = [aws_api_gateway_usage_plan.usage_plan]
}

resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = aws_api_gateway_stage.stage.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled        = true
    logging_level          = "INFO"
    caching_enabled        = true
    cache_ttl_in_seconds   = 300
    cache_data_encrypted   = true
  }
}