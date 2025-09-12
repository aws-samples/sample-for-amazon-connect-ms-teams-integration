# ----------------------------------------------------------
#                Common variables
# ----------------------------------------------------------
# Region where you want to deploy this solution.  Make sure that you have access to
# Bedrock service in this region if you plan to use Bedrock based LLMs
region = "YOUR_AWS_REGION"

# ----------------------------------------------------------
#                Blueprint RAG Chat Bot API
# ----------------------------------------------------------
api_is_private      = false
api_vpc_endpoint_id = "" # if api_is_private=true, api_vpc_endpoint_id is required
api_name            = "connect-chat-api"
api_description     = "REST API that accepts messages from chat clients and invokes Amazon Connect"
stage_name          = "dev"
api_resources = [
  {
    path_part                      = "slack"
    http_method                    = "POST"
    lambda_function_name           = "connect-api-lambda"
    lambda_proxy_arn               = "arn:aws:lambda:us-east-1:YOUR_AWS_ACCOUNT:function:connect-api-lambda"
    api_gateway_execution_role_arn = "arn:aws:iam::YOUR_AWS_ACCOUNT:role/YOUR_API_GATEWAY_EXECUTION_ROLE"
  },
  {
    path_part                      = "teams"
    http_method                    = "POST"
    lambda_function_name           = "connect-api-lambda"
    lambda_proxy_arn               = "arn:aws:lambda:us-east-1:YOUR_AWS_ACCOUNT:function:connect-api-lambda"
    api_gateway_execution_role_arn = "arn:aws:iam::YOUR_AWS_ACCOUNT:role/YOUR_API_GATEWAY_EXECUTION_ROLE"
  },
  {
    path_part                      = "web"
    http_method                    = "POST"
    lambda_function_name           = "connect-api-lambda"
    lambda_proxy_arn               = "arn:aws:lambda:us-east-1:YOUR_AWS_ACCOUNT:function:connect-api-lambda"
    api_gateway_execution_role_arn = "arn:aws:iam::YOUR_AWS_ACCOUNT:role/YOUR_API_GATEWAY_EXECUTION_ROLE"
  },
]
