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

module "this_layer" {
  source                      = "../../../deployment/terraform/module/layer"
  layer_name                  = var.this_layer_name
  layer_description           = var.this_layer_description
  layer_source_code_file_path = var.this_layer_source_code_file_path
  runtimes                    = var.this_layer_runtimes
  compatible_architectures    = var.this_layer_compatible_arch
}
