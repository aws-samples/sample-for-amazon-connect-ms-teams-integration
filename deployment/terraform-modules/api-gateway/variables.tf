variable "region" {
  type        = string
  description = "REST API region"
}

variable "api_name" {
  type        = string
  description = "REST API name"
}

variable "api_description" {
  type        = string
  description = "REST API description"
  default     = ""
}

variable "api_is_private" {
  type        = bool
  description = "REST API is PRIVATE"
  default     = false
}

variable "allowlisted_ips" {
  type        = list(string)
  description = "Whitelist of ip that can call the API"
  default     = []
}

variable "api_vpc_endpoint_id" {
  type        = string
  description = "Private REST API VPC Endpoint Id"
  default     = ""
}

variable "stage_name" {
  type        = string
  description = "API deployment stage name"
}

variable "api_resources" {
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

# ----------------------------------------------------------
#                         Tags
# ----------------------------------------------------------
variable "rest_api_tags" {
  type        = map(string)
  description = "A map containing tags. Both the key and value must be strings."
  default     = {}
}

variable "api_key_tags" {
  type        = map(string)
  description = "A map containing tags. Both the key and value must be strings."
  default     = {}
}

variable "usage_plan_tags" {
  type        = map(string)
  description = "A map containing tags. Both the key and value must be strings."
  default     = {}
}

variable "stage_tags" {
  type        = map(string)
  description = "A map containing tags. Both the key and value must be strings."
  default     = {}
}

variable "cloudwatch_encryption_key" {
  type = string
  description = "KMS key to encrypt cloudwatch logs"
}

variable "cloudwatch_log_retention_days" {
  type = number
  description = "Number of days for the CloudWatch log retention"
  default = 365
}