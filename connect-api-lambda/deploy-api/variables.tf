# ----------------------------------------------------------
#                Common variables
# ----------------------------------------------------------
variable "region" {
  type = string
}

# ----------------------------------------------------------
#          Blueprint RAG Chat Bot API variable
# ----------------------------------------------------------
variable "api_name" {
  type = string
}

variable "api_description" {
  type    = string
  default = ""
}

variable "api_is_private" {
  type        = bool
  description = "REST API is PRIVATE"
  default     = false
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
