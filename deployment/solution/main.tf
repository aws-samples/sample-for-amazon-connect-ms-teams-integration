provider "aws" {
  region = var.aws_region  # or your preferred region
}

data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
}

# -----------------------------------------------------
#                 DynamoDB table
# -----------------------------------------------------

resource "aws_dynamodb_table" "dynamodb_table" {
  name           = var.chat_session_dynamodb_table_name
  billing_mode   = var.billing_mode
  read_capacity  = var.billing_mode == "PROVISIONED" ? var.read_capacity : null
  write_capacity = var.billing_mode == "PROVISIONED" ? var.write_capacity : null

  dynamic "attribute" {
    for_each = var.attributes

    content {
      name = attribute.value.name
      type = attribute.value.type
    }
  }

  hash_key  = var.hash_key

  ttl {
    attribute_name = var.ttl.attribute_name
    enabled        = var.ttl.enabled
  }

  global_secondary_index {
    name               = "contact_id-index"
    hash_key           = "contact_id"
    read_capacity  = var.billing_mode == "PROVISIONED" ? var.read_capacity : null
    write_capacity = var.billing_mode == "PROVISIONED" ? var.write_capacity : null
    projection_type    = "ALL"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.solution_kms_key.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_kms_key" "solution_kms_key" {
  description             = "KMS key for DynamoDB table encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${local.account_id}:root"
        }
        Action = "kms:*"
        Resource = "*"
      },
      {
        Sid = "Allow Lambda Functions to use the key"
        Effect = "Allow"
        Principal = {
          AWS = [
            aws_iam_role.connect_api_lambda_role.arn,
            aws_iam_role.connect_stream_lambda_role.arn
          ]
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow Connect service-linked role to use the key"
        Effect = "Allow"
        Principal = {
          AWS = aws_connect_instance.teams_integration_connect_instance.service_role
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey*"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow Amazon Connect to use the key"
        Effect = "Allow"
        Principal = {
          Service = "connect.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey*"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "sns.${var.aws_region}.amazonaws.com"
          }
        }
      },
      {
        Sid    = "Allow CloudWatch Logs to use the key"
        Effect = "Allow"
        Principal = {
          Service = "logs.${var.aws_region}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt*",
          "kms:Decrypt*",
          "kms:ReEncrypt*", 
          "kms:GenerateDataKey*",
          "kms:Describe*"
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn": "arn:aws:logs:${var.aws_region}:${local.account_id}:*"
          }
        }
      }          
    ]
  })
}

resource "aws_kms_alias" "dynamodb_key_alias" {
  name          = "alias/dynamodb-key"
  target_key_id = aws_kms_key.solution_kms_key.key_id
}

# -----------------------------------------------------
#                 Chat Clients SDK Layer
# -----------------------------------------------------

resource "aws_lambda_layer_version" "chat_clients_sdk_layer" {
  filename            = var.chat_clients_sdk_layer_zip_path
  layer_name          = var.chat_clients_sdk_layer_name
  compatible_runtimes = [var.chat_clients_sdk_layer_runtime]
  compatible_architectures = [var.chat_clients_sdk_layer_architecture]
  skip_destroy        = true
  source_code_hash = filebase64sha256(var.chat_clients_sdk_layer_zip_path)
}

# -----------------------------------------------------
#                 Connect API Lambda
# -----------------------------------------------------

# Create a zip file of your Lambda function code
data "archive_file" "connect_api_lambda_zip" {
  type        = "zip"
  source_dir  = var.connect_api_lambda_source_code_path
  output_path = "../output/connect_api_lambda_function.zip"
  excludes    = ["__pycache__", "*.pyc", "*.pyo"]
}

# IAM role for the Lambda function
resource "aws_iam_role" "connect_api_lambda_role" {
  name = var.connect_api_lambda_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "connect_api_lambda_policy" {
  name = "${var.connect_api_lambda_role_name}-policy"
  role = aws_iam_role.connect_api_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${local.account_id}:log-group:/aws/lambda/${var.connect_api_lambda_function_name}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Scan",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.dynamodb_table.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.chat_sns_topic.arn
      },
      {
        Effect = "Allow"
        Action = [
          "connect:StartChatContact",
          "connect:StartContactStreaming"
        ]
        Resource = [
          "arn:aws:connect:${var.aws_region}:${local.account_id}:instance/${aws_connect_instance.teams_integration_connect_instance.id}",
          "arn:aws:connect:${var.aws_region}:${local.account_id}:instance/${aws_connect_instance.teams_integration_connect_instance.id}/*",
          "arn:aws:connect:${var.aws_region}:${local.account_id}:instance/${aws_connect_instance.teams_integration_connect_instance.id}/contact/*"
        ]
      }
    ]
  })
}

# Define the Lambda function resource
resource "aws_lambda_function" "connect_api_lambda" {
  filename         = data.archive_file.connect_api_lambda_zip.output_path
  function_name    = var.connect_api_lambda_function_name
  role             = aws_iam_role.connect_api_lambda_role.arn
  handler          = var.connect_api_lambda_handler
  layers = [aws_lambda_layer_version.chat_clients_sdk_layer.arn]
  source_code_hash = data.archive_file.connect_api_lambda_zip.output_base64sha256
  runtime          = var.connect_api_lambda_runtime
  architectures = [var.connect_api_lambda_architecture]
  timeout = var.connect_api_lambda_timeout
  kms_key_arn = aws_kms_key.solution_kms_key.arn
  publish = true
  reserved_concurrent_executions = var.connect_api_lambda_reserved_concurrent_executions
  code_signing_config_arn = aws_lambda_code_signing_config.lambda_signing_config.arn
  tracing_config {
    mode = "Active"
  }

  # If you have any environment variables
  environment {
    variables = merge({
      CONNECT_SESSION_DDB_TABLE_NAME = var.chat_session_dynamodb_table_name
      CONNECT_SESSION_DDB_TABLE_TTL = var.connect_session_ddb_table_ttl
      TEAMS_APP_CLIENT_ID = var.teams_app_client_id
      TEAMS_APP_CLIENT_SECRET = var.teams_app_client_secret
      STREAMING_ENDPOINT_ARN = aws_sns_topic.chat_sns_topic.arn
      CONNECT_INSTANCE_ID = aws_connect_instance.teams_integration_connect_instance.id
      CONNECT_CONTACT_FLOW_ID = aws_connect_contact_flow.connect_ccp_flow.contact_flow_id
      TEAMS_IS_SINGLE_TENANT_APP = var.teams_is_single_tenant_app
      USER_CHAT_CLIENT_TYPE = var.user_chat_client_type
      TEAMS_TENANT_ID = var.teams_tenant_id
    }, var.connect_api_lambda_env_variables)
  }
}

resource "aws_lambda_provisioned_concurrency_config" "connect_api_lambda_concurrency" {
  function_name                     = aws_lambda_function.connect_api_lambda.function_name
  provisioned_concurrent_executions = var.lambda_provisioned_concurrency
  qualifier                        = aws_lambda_function.connect_api_lambda.version
}

# Attach necessary policies to the IAM role
resource "aws_iam_role_policy_attachment" "connect_api_lambda_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.connect_api_lambda_role.name
}

# -----------------------------------------------------
#                 Lambda Code Signing
# -----------------------------------------------------

# Create a signing profile for Lambda code signing
resource "aws_signer_signing_profile" "lambda_signing_profile" {
  platform_id = "AWSLambda-SHA384-ECDSA"
}

# Create a code signing config with "Warn" policy for easier adoption
resource "aws_lambda_code_signing_config" "lambda_signing_config" {
  allowed_publishers {
    signing_profile_version_arns = [aws_signer_signing_profile.lambda_signing_profile.version_arn]
  }

  policies {
    untrusted_artifact_on_deployment = "Warn"  # Use "Warn" instead of "Enforce" for easier adoption
  }
}

# -----------------------------------------------------
#                 Connect stream Lambda
# -----------------------------------------------------

data "archive_file" "connect_stream_lambda_zip" {
  type        = "zip"
  source_dir  = var.connect_stream_lambda_source_code_path
  output_path = "../output/connect_stream_lambda_function.zip"
  excludes    = ["__pycache__", "*.pyc", "*.pyo"]
}

# IAM role for the Lambda function
resource "aws_iam_role" "connect_stream_lambda_role" {
  name = var.connect_stream_lambda_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Define the Lambda function resource
resource "aws_lambda_function" "connect_stream_lambda" {
  filename         = data.archive_file.connect_stream_lambda_zip.output_path
  function_name    = var.connect_stream_lambda_function_name
  role             = aws_iam_role.connect_stream_lambda_role.arn
  handler          = var.connect_stream_lambda_handler
  source_code_hash = data.archive_file.connect_stream_lambda_zip.output_base64sha256
  runtime          = var.connect_stream_lambda_runtime
  layers = [aws_lambda_layer_version.chat_clients_sdk_layer.arn]
  kms_key_arn = aws_kms_key.solution_kms_key.arn
  timeout = var.connect_stream_lambda_timeout
  reserved_concurrent_executions = var.connect_stream_lambda_reserved_concurrent_executions
  publish = true
  code_signing_config_arn = aws_lambda_code_signing_config.lambda_signing_config.arn
  tracing_config {
    mode = "Active"
  }

  # If you have any environment variables
  environment {
    variables = merge({
      # LOG_LEVEL = var.log_level
      CONNECT_SESSION_DDB_TABLE_NAME = var.chat_session_dynamodb_table_name
      CONNECT_SESSION_DDB_TABLE_TTL = var.connect_session_ddb_table_ttl
      TEAMS_APP_CLIENT_ID = var.teams_app_client_id
      TEAMS_APP_CLIENT_SECRET = var.teams_app_client_secret
      USER_CHAT_CLIENT_TYPE = var.user_chat_client_type
      TEAMS_IS_SINGLE_TENANT_APP = var.teams_is_single_tenant_app
      TEAMS_TENANT_ID = var.teams_tenant_id
    }, var.connect_stream_lambda_env_variables)
  }
}

resource "aws_lambda_provisioned_concurrency_config" "connect_stream_lambda_concurrency" {
  function_name                     = aws_lambda_function.connect_stream_lambda.function_name 
  provisioned_concurrent_executions = var.lambda_provisioned_concurrency
  qualifier                        = aws_lambda_function.connect_stream_lambda.version
}  

# Attach necessary policies to the IAM role
resource "aws_iam_role_policy_attachment" "connect_stream_lambda_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.connect_stream_lambda_role.name
}

resource "aws_iam_role_policy" "connect_stream_lambda_policy" {
  name = "${var.connect_stream_lambda_role_name}-policy"
  role = aws_iam_role.connect_stream_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${local.account_id}:log-group:/aws/lambda/${var.connect_stream_lambda_function_name}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Scan",
          "dynamodb:Query"
        ]
        Resource = [
          aws_dynamodb_table.dynamodb_table.arn,
          "${aws_dynamodb_table.dynamodb_table.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.chat_sns_topic.arn
      },
      {
        Effect = "Allow"
        Action = [
          "connect:StartChatContact",
          "connect:StartContactStreaming"
        ]
        Resource = [
          "arn:aws:connect:${var.aws_region}:${local.account_id}:instance/${aws_connect_instance.teams_integration_connect_instance.id}",
          "arn:aws:connect:${var.aws_region}:${local.account_id}:instance/${aws_connect_instance.teams_integration_connect_instance.id}/*",
          "arn:aws:connect:${var.aws_region}:${local.account_id}:instance/${aws_connect_instance.teams_integration_connect_instance.id}/contact/*"
        ]
      }
    ]
  })
}


# -----------------------------------------------------
#                 SNS Topic & subscription
# -----------------------------------------------------

resource "aws_sns_topic" "chat_sns_topic" {
  name              = var.sns_topic_name
  kms_master_key_id = aws_kms_key.solution_kms_key.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowConnectToPublishToSNS"
        Effect = "Allow"
        Principal = {
          Service = "connect.amazonaws.com"
        }
        Action   = "sns:Publish"
        Resource = "arn:aws:sns:${var.aws_region}:${local.account_id}:${var.sns_topic_name}"
        Condition = {
          ArnLike = {
            "aws:SourceArn": "arn:aws:connect:${var.aws_region}:${local.account_id}:instance/${aws_connect_instance.teams_integration_connect_instance.id}"
          }
        }
      }
    ]
  })
}

module "sns_subscription" {
  source = "../terraform-modules/sns-subscription-lambda"
  sns_topic_arn = aws_sns_topic.chat_sns_topic.arn
  region = var.aws_region
  lambda_function_name = var.connect_stream_lambda_function_name
  account_id = local.account_id
}

# -----------------------------------------------------
#                     API Gateway
# -----------------------------------------------------

resource "aws_iam_role" "api_gateway_execution_role" {
  name = var.connect_rest_api_execution_role_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = var.api_gateway_role_principal_name
        }
      },
    ]
  })
}

resource "aws_iam_role_policy" "lambda_execution_policy" {
  name = "lambda_execution_policy"
  role = aws_iam_role.api_gateway_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.connect_api_lambda.arn,
          "${aws_lambda_function.connect_api_lambda.arn}:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
              # basic permissions for API Gateway service to send logs to CloudWatch
              "logs:CreateLogGroup",
              "logs:CreateLogStream",
              "logs:DescribeLogGroups",
              "logs:DescribeLogStreams",
              "logs:PutLogEvents",
              "logs:GetLogEvents",
              "logs:FilterLogEvents",
              # borrowed from managed policy "APIGatewayAWSProxyExecRole"
              "logs:CreateLogDelivery",
              "logs:GetLogDelivery",
              "logs:UpdateLogDelivery",
              "logs:DeleteLogDelivery",
              "logs:ListLogDeliveries",
            ]
        Resource = [
          "*"
        ]
      }
    ]
  })
}

module "connect_api" {
  source = "../terraform-modules/api-gateway"
  stage_name = var.stage_name
  region = var.aws_region
  api_name = var.connect_rest_api_name
  allowlisted_ips     = var.allowlisted_ips
  cloudwatch_encryption_key = aws_kms_key.solution_kms_key.arn
  api_resources = [
    {
      path_part                      = "teams"
      http_method                    = "POST"
      lambda_function_name           = var.connect_api_lambda_function_name
      lambda_proxy_arn               = "${aws_lambda_function.connect_api_lambda.arn}"
      lambda_invoke_arn              = "${aws_lambda_function.connect_api_lambda.invoke_arn}"
      api_gateway_execution_role_arn = "${aws_iam_role.api_gateway_execution_role.arn}"
    },
    {
      path_part                      = "web"
      http_method                    = "POST"
      lambda_function_name           = var.connect_api_lambda_function_name
      lambda_proxy_arn               = "${aws_lambda_function.connect_api_lambda.arn}"
      lambda_invoke_arn              = "${aws_lambda_function.connect_api_lambda.invoke_arn}"
      api_gateway_execution_role_arn = "${aws_iam_role.api_gateway_execution_role.arn}"
    }
  ]
}



# ------------------------------------------------------
#                     Lex Bot
# ------------------------------------------------------

resource "aws_iam_role" "lex_bot_iam_role" {
  name = var.lex_bot_iam_role_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lexv2.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lex_bot_iam_role_policy_statement" {
  role       = aws_iam_role.lex_bot_iam_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonLexFullAccess"
}

resource "aws_lexv2models_bot" "amazon_connect_lex_bot" {
  name                        = var.lex_bot_name
  idle_session_ttl_in_seconds = 60
  role_arn                    = aws_iam_role.lex_bot_iam_role.arn

  data_privacy {
    child_directed = true
  }
}


resource "aws_lexv2models_bot_locale" "english_locale" {
  locale_id                        = var.lex_bot_locale
  bot_id                           = aws_lexv2models_bot.amazon_connect_lex_bot.id
  bot_version                      = var.lex_bot_version
  n_lu_intent_confidence_threshold = var.lex_bot_confidence_threshold
}

resource "aws_lexv2models_bot_version" "v1" {
  bot_id = aws_lexv2models_bot.amazon_connect_lex_bot.id
  locale_specification = {
    (aws_lexv2models_bot_locale.english_locale.locale_id) = {
      source_bot_version = var.lex_bot_version
    }
  }
}

resource "aws_lexv2models_intent" "agent_intent" {
  bot_id      = aws_lexv2models_bot.amazon_connect_lex_bot.id
  bot_version = var.lex_bot_version
  name        = var.agent_intent_name
  locale_id   = aws_lexv2models_bot_locale.english_locale.locale_id

  dynamic "sample_utterance" {
    for_each = var.agent_intent_utterances
    content {
      utterance = sample_utterance.value
    }
  }
}

resource "aws_lexv2models_intent" "password_reset_intent" {
  bot_id      = aws_lexv2models_bot.amazon_connect_lex_bot.id
  bot_version = var.lex_bot_version
  name        = var.password_reset_intent_name
  locale_id   = aws_lexv2models_bot_locale.english_locale.locale_id

  dynamic "sample_utterance" {
    for_each = var.password_reset_intent_utterances
    content {
      utterance = sample_utterance.value
    }
  }
}

resource "aws_lexv2models_intent" "ticket_status_intent" {
  bot_id      = aws_lexv2models_bot.amazon_connect_lex_bot.id
  bot_version = var.lex_bot_version
  name        = var.ticket_status_intent_name
  locale_id   = aws_lexv2models_bot_locale.english_locale.locale_id

  dynamic "sample_utterance" {
    for_each = var.ticket_status_intent_utterances
    content {
      utterance = sample_utterance.value
    }
  }
}

resource "aws_lexv2models_intent" "goodbye_intent" {
  bot_id      = aws_lexv2models_bot.amazon_connect_lex_bot.id
  bot_version = var.lex_bot_version
  name        = var.goodbye_intent_name
  locale_id   = aws_lexv2models_bot_locale.english_locale.locale_id

  dynamic "sample_utterance" {
    for_each = var.goodbye_intent_utterances
    content {
      utterance = sample_utterance.value
    }
  }
}

data "external" "lex_bot_alias" {
  program = ["bash", "-c", <<EOT
    ALIAS_ID=$(aws lexv2-models list-bot-aliases \
      --bot-id ${aws_lexv2models_bot.amazon_connect_lex_bot.id} \
      --region ${var.aws_region} \
      --query "botAliasSummaries[?botAliasName=='TestBotAlias'].botAliasId" \
      --output text)
    echo "{\"alias_id\": \"$ALIAS_ID\"}"
  EOT
  ]

  query = {
    dummy = "dummy"
  }

  depends_on = [aws_lexv2models_bot.amazon_connect_lex_bot]
}

locals {
  bot_alias_arn = "arn:aws:lex:${var.aws_region}:${local.account_id}:bot-alias/${aws_lexv2models_bot.amazon_connect_lex_bot.id}/${data.external.lex_bot_alias.result["alias_id"]}"
}

# Associate Lex Bot v2 with Connect flow using aws cli command
# workaround for associating Lex v2 bots with Amazon Connect as
# terraform doesn't have the feature yet
# https://github.com/hashicorp/terraform-provider-aws/issues/30869

resource "null_resource" "lex_bot_association" {
  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command     = "aws connect associate-bot --instance-id ${aws_connect_instance.teams_integration_connect_instance.id} --lex-v2-bot AliasArn=${local.bot_alias_arn} --region ${var.aws_region}"
  }

  triggers = {
    bot_alias_arn = local.bot_alias_arn
    instance_id   = aws_connect_instance.teams_integration_connect_instance.id
  }

  depends_on = [
    data.external.lex_bot_alias,
    aws_connect_instance.teams_integration_connect_instance
  ]
}

# -----------------------------------------------------
#           Amazon Connect Instance and flow
# -----------------------------------------------------

# First, create the Amazon Connect instance
resource "aws_connect_instance" "teams_integration_connect_instance" {
  identity_management_type = var.connect_identity_management_type # or "SAML" or "EXISTING_DIRECTORY"
  inbound_calls_enabled   = true
  outbound_calls_enabled  = true
  instance_alias         = var.connect_instance_alias  # This must be globally unique
}

resource "aws_lambda_permission" "connect_lambda_permission" {
  statement_id  = "AllowConnectInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.connect_api_lambda.function_name
  principal     = "connect.amazonaws.com"
  source_arn    = aws_connect_instance.teams_integration_connect_instance.arn
}

resource "aws_iam_role_policy" "connect_lambda_invoke_policy" {
  name = var.connect_lambda_invoke_policy_name
  role = aws_iam_role.connect_api_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "connect:StartContactStreaming",
          "connect:StopContactStreaming",
          "connect:GetContactAttributes",
          "connect:UpdateContactAttributes",
          "connect:CreateParticipant",
          "connect:DisconnectParticipant",
          "connect:GetCurrentMetricData",
          "connect:GetMetricData",
          "connect:StartOutboundVoiceContact",
          "connect:StopContact",
          "connect:DescribeContact",
          "connect:ListContactFlows",
          "connect:StartChatContact",
          "connect:StartTaskContact",
          "connect:UpdateContactFlowContent",
          "connect:UpdateContactFlowName",
          "connect:DescribeContactFlow",
          "connect:ListContactFlowModules",
          "connect:CreateContactFlowModule",
          "connect:UpdateContactFlowModule",
          "connect:DeleteContactFlowModule",
          "connect:DescribeContactFlowModule"
        ]
        Resource = [
          "arn:aws:connect:${var.aws_region}:${local.account_id}:instance/${aws_connect_instance.teams_integration_connect_instance.id}",
          "arn:aws:connect:${var.aws_region}:${local.account_id}:instance/${aws_connect_instance.teams_integration_connect_instance.id}/*",
          "arn:aws:connect:${var.aws_region}:${local.account_id}:instance/${aws_connect_instance.teams_integration_connect_instance.id}/contact/*"
        ]
      }
    ]
  })
}

data "aws_connect_contact_flow" "disconnect_flow" {
  instance_id = aws_connect_instance.teams_integration_connect_instance.id
  name        = var.connect_sample_disconnect_flow_name
}

data "aws_connect_contact_flow" "queue_flow" {
  instance_id = aws_connect_instance.teams_integration_connect_instance.id
  name        = var.connect_sample_queue_flow_name
}

resource "aws_connect_contact_flow" "connect_ccp_flow" {
  instance_id = aws_connect_instance.teams_integration_connect_instance.id
  name       = var.connect_flow_name
  type       = var.connect_flow_type
  description = var.connect_flow_description
  content    = templatefile(var.connect_flow_json_path, {
    lex_bot_name = var.lex_bot_name
    lex_bot_alias_arn = local.bot_alias_arn
    disconnect_flow_id = data.aws_connect_contact_flow.disconnect_flow.arn
    queue_flow = data.aws_connect_contact_flow.queue_flow.arn
  })
  depends_on = [ aws_connect_instance.teams_integration_connect_instance ]
}
