#!/bin/sh

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

## initialize and do some pre-flight checks
if [ -z "$AWS_PROFILE" -o \
    -z "$AWS_REGION" -o \
    -z "$AWS_ACCOUNT_ID" -o \
    -z "$TERRAFORM_COMMAND" -o \
    -z "$API_NAME" -o \
    -z "$API_DESCRIPTION" -o \
    -z "$API_STAGE_NAME" -o \
    -z "$LAMBDA_PROXY_FUNCTION_NAME" -o \
    -z "$LAMBDA_PROXY_FUNCTION_ARN" -o \
    -z "$IS_PRIVATE_API" ]; then
    echo "Missing environment variables.  Ensure following environment variables are set"
    echo "  AWS_PROFILE"
    echo "  AWS_REGION"
    echo "  AWS_ACCOUNT_ID"
    echo "  TERRAFORM_COMMAND"
    echo "  API_NAME"
    echo "  API_DESCRIPTION"
    echo "  API_STAGE_NAME"
    echo "  LAMBDA_PROXY_FUNCTION_NAME"
    echo "  LAMBDA_PROXY_FUNCTION_ARN"
    echo "  LEX_BOT_ALIAS_ID"
    echo "  IS_PRIVATE_API"
    echo
    echo "Following are optional environment variables.  Set these to control additional LLM behaviour"
    echo "  API_VPC_ENDPOINT_ID"
    echo "  API_GATEWAY_EXECUTION_ROLE_ARN"
    echo
    exit 1
fi

## Change variables as necessary
terraform_solution_path="./deploy-api"

## !IMPORTANT! DO NOT MODIFY BELOW THIS LINE
WORKING_DIR="$(pwd)"

## pre-flight checks
if [ -d .venv/bin ]; then
    . .venv/bin/activate
else
    echo "WARNING: .venv/bin not found. Please install the python virtual environment."
    echo "         Follow the project documentation for more information."
    echo "         Also check the Prerequisites documentation."
fi

if [ -z "$VIRTUAL_ENV" ]; then
    project_name=$(basename $WORKING_DIR)
    echo "You are not running in a .venv environment. Click the + icon on the top-right to launch a .venv in '${project_name}'!"
    exit 1
fi

# check $TERRAFORM_COMMAND must be "apply" or "destroy".  Raise error otherwise
if [ "${TERRAFORM_COMMAND}" != "apply" -a \
     "${TERRAFORM_COMMAND}" != "destroy" ]; then
     echo "Invalid TERRAFORM_COMMAND: '${TERRAFORM_COMMAND}'"
     echo "TERRAFORM_COMMAND must be either 'apply' or 'destroy'.  Commands are case-sensitive."
     rm -rf /tmp/$$.*
     exit 1
fi

## check for all required CLI utilities, i.e. terraform
terraform -version >/tmp/$$.terraform.version.log 2>&1
if [ $? -ne 0 ]; then
    echo "terraform command not found.  Please install terraform cli."
    rm -rf /tmp/$$.*
    exit 1
fi
echo "All required deployment utilities found."

# show some stats
echo
echo "API Properties:"
echo "  name: ${API_NAME}"
echo "  description: ${API_DESCRIPTION}"
echo "  stage: ${API_STAGE_NAME}"
echo "  lambda_function: ${LAMBDA_PROXY_FUNCTION_NAME}"
echo "  lambda_function_arn: ${LAMBDA_PROXY_FUNCTION_ARN}"
echo "  is_private_api: ${IS_PRIVATE_API}"

echo
echo "Environment Variables:"
echo "  WORKING_DIR: ${WORKING_DIR}"
echo "  AWS_PROFILE: ${AWS_PROFILE}"
echo "  AWS_REGION: ${AWS_REGION}"
echo "  AWS_ACCOUNT_ID: ${AWS_ACCOUNT_ID}"
echo "  TERRAFORM_COMMAND: ${TERRAFORM_COMMAND}"

if [ ! -z "${API_VPC_ENDPOINT_ID}" ]; then
    echo "  API_VPC_ENDPOINT_ID: ${API_VPC_ENDPOINT_ID}"
fi
if [ ! -z "${API_GATEWAY_EXECUTION_ROLE_ARN}" ]; then
    echo "  API_GATEWAY_EXECUTION_ROLE_ARN: ${API_GATEWAY_EXECUTION_ROLE_ARN}"
fi
echo

## deploy api

# create conditional variable values (if any)
api_vpc_endpoint_id=""
if [ ! -z "${API_VPC_ENDPOINT_ID}" ]; then
    api_vpc_endpoint_id="${API_VPC_ENDPOINT_ID}"
fi
if [ ! -z "${API_GATEWAY_EXECUTION_ROLE_ARN}" ]; then
    api_gateway_execution_role_arn="${API_GATEWAY_EXECUTION_ROLE_ARN}"
fi

# create a temporary tarraform .tfvars file
cat >/tmp/$$.tfvars <<EOF
region = "${AWS_REGION}"
api_is_private      = ${IS_PRIVATE_API}
api_vpc_endpoint_id = "${api_vpc_endpoint_id}"
api_name            = "${API_NAME}"
api_description     = "${API_DESCRIPTION}"
stage_name          = "${API_STAGE_NAME}"
api_resources = [
  {
    path_part                      = "slack"
    http_method                    = "POST"
    lambda_function_name           = "${LAMBDA_PROXY_FUNCTION_NAME}"
    lambda_proxy_arn               = "arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${LAMBDA_PROXY_FUNCTION_NAME}"
    api_gateway_execution_role_arn = "${api_gateway_execution_role_arn}"
  },
  {
    path_part                      = "web"
    http_method                    = "POST"
    lambda_function_name           = "${LAMBDA_PROXY_FUNCTION_NAME}"
    lambda_proxy_arn               = "arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${LAMBDA_PROXY_FUNCTION_NAME}"
    api_gateway_execution_role_arn = "${api_gateway_execution_role_arn}"
  }
]
EOF

echo
echo "terraform tfvars file:"
echo "----------------------------------------------------------"
cat /tmp/$$.tfvars
echo "----------------------------------------------------------"
echo
echo "terraform is executing '${TERRAFORM_COMMAND}' command using tfvars above"
(
    cd "${terraform_solution_path}";
    terraform init;
    terraform $TERRAFORM_COMMAND -var-file=/tmp/$$.tfvars -auto-approve;
) > /tmp/$$.terraform.log 2>&1
if [ $? -ne 0 ]; then
    echo "Error: Unable to deploy lambda"
    cat /tmp/$$.terraform.log
    rm -rf /tmp/$$.*
    exit 1
fi

## clean up
cat /tmp/$$.terraform.log
rm -rf /tmp/$$.*
echo
echo "done!"
