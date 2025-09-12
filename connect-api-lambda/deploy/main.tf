terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

  }

  required_version = ">= 1.2.0"
}

provider "aws" {
  region = var.region
}

module "lambda_rag" {
  source                            = "../../../deployment/terraform/module/lambda"
  s3_lambda_source_code_bucket_name = var.lambda_s3_source_bucket_name
  s3_lambda_source_code_bucket_key  = var.lambda_s3_source_bucket_key
  function_version                  = var.lambda_function_version
  function_name                     = var.lambda_function_name
  function_description              = var.lambda_function_description
  lambda_source_code_path           = var.lambda_source_code_path
  role_arn                          = var.lambda_role_arn
  handler                           = var.lambda_handler
  runtime                           = var.lambda_runtime
  architecture                      = var.lambda_architecture
  mem_size                          = var.lambda_mem_size
  timeout                           = var.lambda_timeout
  layers_arn                        = var.lambda_layer_arn
  subnet_id_list_for_lambda         = var.lambda_vpc_subnet_id_list
  sg_id_list_for_lambda             = var.lambda_vpc_sg_id_list
  environment_variables             = var.lambda_environment_variables
}
