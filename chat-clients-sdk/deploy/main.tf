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

resource "aws_lambda_layer_version" "this_layer" {
  filename                 = var.this_layer_source_code_file_path
  layer_name               = var.this_layer_name
  description              = var.this_layer_description
  compatible_runtimes      = var.this_layer_runtimes
  compatible_architectures = var.this_layer_compatible_arch
  skip_destroy             = true
  source_code_hash         = filebase64sha256(var.this_layer_source_code_file_path)
}
