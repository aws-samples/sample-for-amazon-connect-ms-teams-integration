# ----------------------------------------------------------
#                Common variables
# ----------------------------------------------------------
# Region where you want to deploy this solution.  Make sure that you have access to
# Bedrock service in this region if you plan to use Bedrock based LLMs
region = "YOUR_AWS_REGION"
# put a ARN if you dont want to generate the role
lambda_role_arn = "arn:aws:iam::YOUR_AWS_ACCOUNT:role/YOUR_LAMBDA_EXECUTION_ROLE_NAME"
# put a ARN if you dont want to generate the role
lambda_layer_arn = ["arn:aws:lambda:YOUR_AWS_REGION:YOUR_AWS_ACCOUNT:layer:chat-clients-sdk:LATEST_DEPLOYED_LAYER_VERSION"]

# ----------------------------------------------------------
#               Common Lambda Config
# ----------------------------------------------------------
lambda_vpc_subnet_id_list    = []
lambda_vpc_sg_id_list        = []
lambda_s3_source_bucket_name = "YOUR_DEPLOYMENT_BUCKET_NAME"
lambda_s3_source_bucket_key  = "YOUR_DEPLOYMENT_BUCKET_PATH"

# ----------------------------------------------------------
#                  Lambda Config
# ----------------------------------------------------------
lambda_function_name        = "blueprint-connect-stream-lambda"
lambda_function_description = "Blueprint Lambda function processes messages from SNS that are emitted by Amazon Connect chat.  It invokes user selected chat client callback API to send messages to front-end."
lambda_function_version     = "0.0.1"
lambda_source_code_path     = "/workspaces/gen-ai/apps/blueprint-connect-stream-lambda"
lambda_handler              = "lambda_function.lambda_handler"
lambda_runtime              = "python3.12"
lambda_architecture         = "x86_64"
lambda_mem_size             = 256
lambda_timeout              = 300
lambda_environment_variables = {
  "LOG_LEVEL"                      = "debug"
  "CONNECT_SESSION_DDB_TABLE_NAME" = "connect-session-table"
  "CONNECT_SESSION_DDB_TABLE_TTL"  = "3600"
  "USER_CHAT_CLIENT_TYPE"          = "SLACK"
  "SLACK_APP_WORKSPACE_TOKEN"      = "xoxb-abcdef"
}
