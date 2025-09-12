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

module "api" {
  source              = "../../../deployment/terraform/module/api-gateway"
  api_name            = var.api_name
  api_description     = var.api_description
  api_is_private      = var.api_is_private
  api_vpc_endpoint_id = var.api_vpc_endpoint_id
  region              = var.region
  stage_name          = var.stage_name
  api_resources       = var.api_resources
}
