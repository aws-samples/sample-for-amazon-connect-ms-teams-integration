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
lambda_function_name        = "connect-api-lambda"
lambda_function_description = "Lambda function that integrates Amazon API Gateway and interacts with Amazon Connect"
lambda_function_version     = "0.0.1"
lambda_source_code_path     = "/workspaces/gen-ai/apps/connect-api-lambda"
lambda_handler              = "lambda_function.lambda_handler"
lambda_runtime              = "python3.12"
lambda_architecture         = "x86_64"
lambda_mem_size             = 256
lambda_timeout              = 300
lambda_environment_variables = {
  "LOG_LEVEL"                      = "debug"
  "CONNECT_INSTANCE_ID"            = "a1234567-aaaa-bbbb-cccc-abcdef123456"
  "CONNECT_CONTACT_FLOW_ID"        = "b1234567-aaaa-bbbb-cccc-123456abcdef"
  "STREAMING_ENDPOINT_ARN"         = "arn:aws:sns:us-west-2:1234567890:CONNECT_STREAM"
  "CONNECT_SESSION_DDB_TABLE_NAME" = "connect-session-table"
  "CONNECT_SESSION_DDB_TABLE_TTL"  = "3600"
  "USER_CHAT_CLIENT_TYPE"          = "SLACK"
}
