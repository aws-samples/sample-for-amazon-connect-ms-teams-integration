# ----------------------------------------------------------
#                Common variables
# ----------------------------------------------------------
variable "region" {
  type = string
}

variable "lambda_role_arn" {
  type        = string
  default     = ""
  description = "Role ARN for the lambda rag."
}

variable "lambda_layer_arn" {
  type        = list(string)
  default     = []
  description = "Lambda Layer ARN for an existing Layer"
}

# ----------------------------------------------------------
#               Common Lambda Config
# ----------------------------------------------------------
variable "lambda_s3_source_bucket_name" {
  type = string
}

variable "lambda_s3_source_bucket_key" {
  type    = string
  default = ""
}

variable "lambda_vpc_subnet_id_list" {
  type        = list(string)
  description = "Sets the subnets in which the lambda will be launched."
  default     = []
}
variable "lambda_vpc_sg_id_list" {
  type        = list(string)
  description = "Security group for the lambda function."
  default     = []
}

# ----------------------------------------------------------
#                    Lambda Config
# ----------------------------------------------------------

variable "lambda_function_name" {
  type        = string
  description = "Name of the rag lambda function that will apear in the AWS function."
}

variable "lambda_function_version" {
  type        = string
  description = "Version is used in zip archive name stored in S3 bucket for deployment."
}

variable "lambda_function_description" {
  type        = string
  description = "Description of the lambda function that apears in the console."
}

variable "lambda_source_code_path" {
  type        = string
  description = "Path to the lambda source code base directory."
}

variable "lambda_handler" {
  type    = string
  default = "lambda_function.py"
}

variable "lambda_runtime" {
  type = string
}

variable "lambda_architecture" {
  type = string
}

variable "lambda_mem_size" {
  type = number
}

variable "lambda_timeout" {
  type = string
}

variable "lambda_environment_variables" {
  type        = map(string)
  description = "A map containing environment variables.  Both the key and value must be strings."
  default     = {}
}
