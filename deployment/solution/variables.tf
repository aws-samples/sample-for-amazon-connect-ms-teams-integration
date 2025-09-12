


variable "aws_region" {
    type = string
    default = "us-east-1"
}

variable "teams_app_client_id" {
  type = string
}

variable "teams_app_client_secret" {
  type = string
}

# ----------------------------------------------------------
#                       DynamoDB table
# ----------------------------------------------------------

variable "chat_session_dynamodb_table_name" {
  type = string
  description = "Amazon DynamoDB table name"
}

variable "billing_mode" {
  type        = string
  description = "Billing mode for the DynamoDB table.The valid values are PROVISIONED and PAY_PER_REQUEST. Defaults to PROVISIONED"
  default     = "PROVISIONED"
}

variable "read_capacity" {
  type        = number
  description = "Read capacity for the DynamoDB table"
  default     = null
}

variable "write_capacity" {
  type        = number
  description = "Write capacity for the DynamoDB table"
  default     = null
}

variable "hash_key" {
  type        = string
  description = "Hash key for the DynamoDB table"
}

variable "range_key" {
  type        = string
  description = "Attribute to use as the range (sort) key. Must also be defined as an attribute"
}

variable "attributes" {
  description = "List of resources for the REST API"
  type = list(object({
    name = string
    type = string
  }))
  default = []
}

variable "ttl" {
  type = object({
    attribute_name = string
    enabled        = bool
    ttl_value      = number
  })
  description = "Value for item TTL and whether it is enabled for the table"
  default = {
    attribute_name = "ttl"
    enabled        = false
    ttl_value      = 86400
  }
}

variable "dynamodb_table_tags" {
  type        = map(string)
  description = "A map containing tags. Both the key and value must be strings."
  default     = {}
}



# Lambda env

variable "log_level" {
  type = string
  default = "info"
}

variable "user_chat_client_type" {
  type = string
}

variable "teams_is_single_tenant_app" {
  type = string
}

variable "teams_tenant_id" {
  type = string
}

variable "connect_session_ddb_table_ttl" {
  type = string
}

variable "lambda_provisioned_concurrency" {
  type = number
  default = 2
}

# ----------------------------------------------------------
#       Lambda: chat-clients-sdk layer
# ----------------------------------------------------------

variable "chat_clients_sdk_layer_name" {
  type        = string
  description = "Name of the Lambda layer"
}

variable "chat_clients_sdk_layer_architecture" {
  type        = string
  description = "CPU architecture for the Lambda function"
  default     = "x86_64"
  validation {
    condition     = contains(["x86_64", "arm64"], var.chat_clients_sdk_layer_architecture)
    error_message = "Architecture must be either x86_64 or arm64"
  }
}

variable "chat_clients_sdk_layer_runtime" {
  type = string
  default = "python3.12"
}

variable "chat_clients_sdk_layer_zip_path" {
  type = string
  default = "../../chat-clients-sdk/build/compressed/chat-clients-sdk-layer-0.0.3.zip"
  # Throw exception if the file is not found
  validation {
    condition     = fileexists(var.chat_clients_sdk_layer_zip_path)
    error_message = "File not found. Did you build the layer?"
  }
}

# ----------------------------------------------------------
#       Lambda: connect-stream-lambda
# ----------------------------------------------------------

variable "connect_stream_lambda_function_name" {
  type        = string
  description = "Name of the Lambda function that processes Connect chat streams"
  default     = "connect-stream-lambda"
}

variable "connect_stream_lambda_function_description" {
  type        = string
  description = "Description of the Lambda function that processes Connect chat messages"
  default     = "Lambda function processes messages from SNS that are emitted by Amazon Connect chat. It invokes user selected chat client callback API to send messages to front-end."
}

variable "connect_stream_lambda_function_version" {
  type        = string
  description = "Version of the Lambda function"
  default     = "0.0.1"
}

variable "connect_stream_lambda_source_code_path" {
  type        = string
  description = "Path to the Lambda function source code"
  default     = "../../connect-api-lambda"
}

variable "connect_stream_lambda_handler" {
  type        = string
  description = "Handler function for the Lambda"
  default     = "lambda_function.lambda_handler"
}

variable "connect_stream_lambda_runtime" {
  type        = string
  description = "Runtime for the Lambda function"
  default     = "python3.12"
}

variable "connect_stream_lambda_architecture" {
  type        = string
  description = "CPU architecture for the Lambda function"
  default     = "x86_64"
  validation {
    condition     = contains(["x86_64", "arm64"], var.connect_stream_lambda_architecture)
    error_message = "Architecture must be either x86_64 or arm64"
  }
}

variable "connect_stream_lambda_reserved_concurrent_executions" {
  type = number
  description = "Reserved Concurrent executions for the Lambda function"
  default = 10
}

variable "connect_stream_lambda_mem_size" {
  type        = number
  description = "Memory size in MB for the Lambda function"
  default     = 256
}

variable "connect_stream_lambda_timeout" {
  type        = number
  description = "Timeout in seconds for the Lambda function"
  default     = 300
}

variable "connect_stream_lambda_env_variables" {
  type = map(string)
  default = {}
  description = "Environment variables for the Lambda function"
}

variable "connect_api_lambda_role_name" {
  type = string
}

# ----------------------------------------------------------
#               Lambda: connect-api-lambda
# ----------------------------------------------------------


variable "connect_api_lambda_function_zip" {
  type = string
  default = "../output/connect_api_lambda_function.zip"
  validation {
    condition = fileexists(var.connect_api_lambda_function_zip)
    error_message = "File not found. Did you build the function?"
  }
}

variable "connect_api_lambda_function_name" {
  type        = string
  description = "Name of the API Lambda function"
  default     = "connect-api-lambda"
}

variable "connect_api_lambda_function_description" {
  type        = string
  description = "Description of the API Lambda function"
  default     = "Amazon API Gateway Lambda Proxy function that interacts with Amazon Connect"
}

variable "connect_api_lambda_function_version" {
  type        = string
  description = "Version of the API Lambda function"
  default     = "0.0.1"
}

variable "connect_api_lambda_source_code_path" {
  type        = string
  description = "Path to the API Lambda function source code"
  default     = "../../connect-api-lambda"
}

variable "connect_api_lambda_handler" {
  type        = string
  description = "Handler function for the API Lambda"
  default     = "lambda_function.lambda_handler"
}

variable "connect_api_lambda_runtime" {
  type        = string
  description = "Runtime for the API Lambda function"
  default     = "python3.12"
}

variable "connect_api_lambda_architecture" {
  type        = string
  description = "CPU architecture for the API Lambda function"
  default     = "x86_64"
  validation {
    condition     = contains(["x86_64", "arm64"], var.connect_api_lambda_architecture)
    error_message = "Architecture must be either x86_64 or arm64"
  }
}

variable "connect_api_lambda_reserved_concurrent_executions" {
  type = number
  description = "Reserved Concurrent executions for the Lambda function"
  default = 10
}

variable "connect_api_lambda_mem_size" {
  type        = number
  description = "Memory size in MB for the API Lambda function"
  default     = 256
}

variable "connect_api_lambda_timeout" {
  type        = number
  description = "Timeout in seconds for the API Lambda function"
  default     = 300
}

variable "connect_api_lambda_env_variables" {
  type = map(string)
  default = {}
  description = "Environment variables for the Lambda function"
}

variable "connect_stream_lambda_role_name" {
  type = string
}

# ----------------------------------------------------------
#                  SNS Topic - standard
# ----------------------------------------------------------

variable "sns_topic_name" {
    type = string
}


# -----------------------------------------------------
#                 API Gateway
# -----------------------------------------------------

variable "connect_rest_api_name" {
  type = string
}

variable "connect_rest_api_description" {
  type = string
}

variable "connect_rest_api_endpoint_configuration" {
  type = list(string)
}

variable "api_is_private" {
  type = bool
}

variable "api_vpc_endpoint_id" {
  type        = string
  description = "Private REST API VPC Endpoint Id"
  default     = ""
}

variable "stage_name" {
  type        = string
  description = "API deployment stage name"
  default     = ""
}

variable "allowlisted_ips" {
  type        = list(string)
  description = "List of IPs to add in the API resource policy allowlisting. If none are specify, there wont be any resource based policy for the API."
  default     = []
}

variable "connect_rest_api_execution_role_name" {
  type = string
  default = "amazon-connect-api-gateway-execution-role"
}

variable "api_gateway_role_principal_name" {
  type        = string
  description = "API Gateway service principal name"
  default     = "apigateway.amazonaws.com"
}


variable "connect_rest_api_resources" {
  description = "List of resources for the REST API"
  type = list(object({
    path_part                      = string
    http_method                    = string
    lambda_function_name           = string
    lambda_proxy_arn               = string
    lambda_proxy_invoke_arn        = optional(string, "")
    api_gateway_execution_role_arn = optional(string, "")
  }))
  default = []
}

variable "rest_api_tags" {
  type = map(string)
  default = {}
}

variable "api_key_tags" {
  type = map(string)
  default = {}
}

variable "usage_plan_tags" {
  type = map(string)
  default = {}
}

variable "stage_tags" {
  type = map(string)
  default = {}
}

# ----------------------------------------------------------
#                  Lex Bot - V2
# ----------------------------------------------------------

variable "lex_bot_name" {
  type = string
}

variable "lex_bot_iam_role_name" {
  type = string
}

variable "lex_bot_locale" {
  type = string
}

variable "lex_bot_version" {
  type = string
}

variable "lex_bot_confidence_threshold" {
  type = number
}

variable "agent_intent_name" {
  type = string
}

variable "agent_intent_utterances" {
  type        = list(string)
  description = "List of sample utterances for the agent intent"
  default = []
}

variable "password_reset_intent_name" {
  type = string
}

variable "password_reset_intent_utterances" {
  type        = list(string)
  description = "List of sample utterances for the password reset intent"
  default = []
}

variable "ticket_status_intent_name" {
  type = string
}

variable "ticket_status_intent_utterances" {
  type        = list(string)
  description = "List of sample utterances for the ticket status intent"
  default = []
}

variable "goodbye_intent_name" {
  type = string
}

variable "goodbye_intent_utterances" {
  type        = list(string)
  description = "List of sample utterances for the goodbye intent"
  default = []
}

# ----------------------------------------------------------
#                  Amazon Connect
# ----------------------------------------------------------

variable "connect_instance_alias" {
  type = string
  description = "This must be globally unique"
}

variable "connect_identity_management_type" {
  type = string
  default = "CONNECT_MANAGED"
}

variable "connect_inbound_calls_enabled" {
  type = bool
}

variable "connect_outbound_calls_enabled" {
  type = bool
}

variable "connect_lambda_invoke_policy_name" {
  type = string
  default = "connect-lambda-invoke-policy"
}

variable "connect_sample_disconnect_flow_name" {
 type = string
 default = "Sample disconnect flow"
}

variable "connect_sample_queue_flow_name" {
  type = string
  default = "Sample queue configurations flow"
}

# Flow details

variable "connect_flow_name" {
  type = string
}

variable "connect_flow_description" {
  type = string
}

variable "connect_flow_json_path" {
    type = string
    default = "../../connect-ccp-flow/example-flow-with-voice.json"
}

variable "connect_flow_type" {
  type = string
}
