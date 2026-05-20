# ----------------------------------------------------------
#                Common variables
# ----------------------------------------------------------
# Region where you want to deploy this solution.  Make sure that you have access to
# Bedrock service in this region if you plan to use Bedrock based LLMs
aws_region      = "us-east-1"

# ----------------------------------------------------------
#               Common Lambda env details
# ----------------------------------------------------------
log_level = "debug"
teams_app_client_id = "YOUR_TEAMS_APP_CLIENT_ID"
teams_app_client_secret = "YOUR_TEAMS_APP_CLIENT_SECRET"
teams_tenant_id = "YOUR_TEAMS_APP_TENANT_ID"
connect_session_ddb_table_ttl = "3600"
teams_is_single_tenant_app = "true"
user_chat_client_type = "TEAMS"


# ----------------------------------------------------------
#               Chat Session DynamoDB table
# ----------------------------------------------------------
chat_session_dynamodb_table_name = "connect-chat-session-table"
billing_mode                 = "PAY_PER_REQUEST"
read_capacity                = 20
write_capacity               = 20
hash_key                     = "id"
range_key                    = "contact_id"
attributes = [
  {
    name = "id"
    type = "S"
  },
  {
    name = "contact_id"
    type = "S"
  }
]
ttl = {
  attribute_name = "ttl"
  enabled        = true
  ttl_value      = 3600 # This value is in seconds and is set to 1 hour.
}

# ----------------------------------------------------------
#               Chat Clients SDK Layer
# ----------------------------------------------------------

chat_clients_sdk_layer_name = "chat-clients-sdk-layer"
chat_clients_sdk_layer_architecture = "x86_64"
chat_clients_sdk_layer_runtime = "python3.12"


# ----------------------------------------------------------
#                     connect-stream-lambda
# ----------------------------------------------------------
connect_stream_lambda_function_name        = "connect-stream-lambda"
connect_stream_lambda_function_description = "Lambda function processes messages from SNS that are emitted by Amazon Connect chat. It invokes user selected chat client callback API to send messages to front-end."
connect_stream_lambda_function_version     = "0.0.1" # check ../../connect-stream-lambda"/pyproject.toml
connect_stream_lambda_source_code_path     = "../../connect-stream-lambda/src"
connect_stream_lambda_handler              = "lambda_function.lambda_handler"
connect_stream_lambda_runtime              = "python3.12"
connect_stream_lambda_architecture         = "x86_64"
connect_stream_lambda_mem_size             = 256
connect_stream_lambda_timeout              = 300
connect_stream_lambda_env_variables = {
  LOG_LEVEL = "debug"
}


connect_stream_lambda_role_name = "connect_stream_lambda_execution_role"

# ----------------------------------------------------------
#                     connect-api-lambda
# ----------------------------------------------------------
connect_api_lambda_function_name        = "connect-api-lambda"
connect_api_lambda_function_description = "Amazon API Gateway Lambda Proxy function that interacts with Amazon Connect"
connect_api_lambda_function_version     = "0.0.1" # check ../../connect-api-lambda"/pyproject.toml
connect_api_lambda_source_code_path     = "../../connect-api-lambda/src"
connect_api_lambda_handler              = "lambda_function.lambda_handler"
connect_api_lambda_runtime              = "python3.12"
connect_api_lambda_architecture         = "x86_64"
connect_api_lambda_mem_size             = 256
connect_api_lambda_timeout              = 300
connect_api_lambda_env_variables = {
  LOG_LEVEL = "debug"
}

connect_api_lambda_role_name = "connect_api_lambda_execution_role"


# ----------------------------------------------------------
#                  SNS Topic - standard
# ----------------------------------------------------------
sns_topic_name = "connect_stream_topic"


# ----------------------------------------------------------
#                      API Gateway
# ----------------------------------------------------------
api_is_private  = false
allowlisted_ips = []
stage_name      = "dev"
connect_rest_api_name = "connect-api-gateway"
connect_rest_api_description = "REST API that accepts messages from chat clients and invokes Amazon Connect."
connect_rest_api_endpoint_configuration = ["REGIONAL"]
connect_rest_api_execution_role_name = "amazon-connect-api-gateway-execution-role"


# ----------------------------------------------------------
#                         Lex Bot
# ----------------------------------------------------------

lex_bot_name = "connect_integration_lex_bot"
lex_bot_iam_role_name = "connect_integration_lex_bot_iam_role"
lex_bot_locale = "en_US"
lex_bot_version = "DRAFT"
lex_bot_confidence_threshold = 0.7

agent_intent_name = "TalkToAgent"
agent_intent_utterances = [
  "I want to speak with an agent",
  "Can I talk to a human",
  "Connect me to an agent",
  "Agent please",
  "Representative",
  "Talk to support"
]

password_reset_intent_name = "ResetPassword"
password_reset_intent_utterances = [
  "I want to reset my password",
  "Can you help me reset my password",
  "Can you help me update my password",
  "I need to update my password",
  "Please reset my password",
  "Password reset"
]

ticket_status_intent_name = "TicketStatus"
ticket_status_intent_utterances = [
  "What is the status of the ticket?",
  "Ticket status",
  "What happened to the ticket"
]

goodbye_intent_name = "GoodBye"
goodbye_intent_utterances = [
  "Goodbye",
  "Bye",
  "See you later",
  "That's all for now",
  "Thanks, bye",
  "I'm done",
  "Exit"
]


# ----------------------------------------------------------
#                Amazon Connect
# ----------------------------------------------------------

connect_instance_alias = "teams-integration-connect-instance"
connect_identity_management_type = "CONNECT_MANAGED"
connect_inbound_calls_enabled = true
connect_outbound_calls_enabled = true

connect_lambda_invoke_policy_name = "connect-lambda-invoke-policy"

connect_sample_disconnect_flow_name = "Sample disconnect flow"
connect_sample_queue_flow_name = "Sample queue configurations flow"

connect_flow_name = "teams-integration-connect-flow"
connect_flow_description = "teams-integration-connect-flow"
connect_flow_json_path = "../../connect-ccp-flow/example-flow-with-voice.json"

connect_flow_type = "CONTACT_FLOW"
