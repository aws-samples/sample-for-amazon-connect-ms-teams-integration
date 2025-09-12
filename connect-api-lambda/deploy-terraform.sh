#!/bin/sh

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

## initialize and do some pre-flight checks
if [ -z "$AWS_PROFILE" -o \
    -z "$AWS_REGION" -o \
    -z "$TERRAFORM_COMMAND" -o \
    -z "$LAMBDA_ROLE_ARN" -o \
    -z "$DEPLOYMENT_BUCKET_NAME" -o \
    -z "$LOG_LEVEL" -o \
    -z "$CONNECT_INSTANCE_ID" -o \
    -z "$CONNECT_CONTACT_FLOW_ID" -o \
    -z "$STREAMING_ENDPOINT_ARN" -o \
    -z "$CONNECT_SESSION_DDB_TABLE_NAME" -o \
    -z "$CONNECT_SESSION_DDB_TABLE_TTL" -o \
    -z "$USER_CHAT_CLIENT_TYPE" ]; then
    echo "Missing environment variables.  Ensure following environment variables are set"
    echo "  AWS_PROFILE"
    echo "  AWS_REGION"
    echo "  TERRAFORM_COMMAND"
    echo "  LAMBDA_ROLE_ARN"
    echo "  DEPLOYMENT_BUCKET_NAME"
    echo "  LOG_LEVEL"
    echo "  CONNECT_INSTANCE_ID"
    echo "  CONNECT_CONTACT_FLOW_ID"
    echo "  STREAMING_ENDPOINT_ARN"
    echo "  CONNECT_SESSION_DDB_TABLE_NAME"
    echo "  CONNECT_SESSION_DDB_TABLE_TTL"
    echo "  USER_CHAT_CLIENT_TYPE"
    echo
    echo "Following are optional environment variables.  Set these to control additional LLM behaviour"
    echo "  LAMBDA_LAYER_ARN"
    echo "  DEPLOYMENT_BUCKET_PATH"
    echo
    echo "Following are optional environment variables.  Set these for deploying lambda with VPC configuration"
    echo "SUBNET_IDS and SECURITY_GROUP_IDS can contain comma-separated list of subnet and security group ids"
    echo "For example, the format for SUBNET_IDS is \"[\"subnet-123\", \"subnet-456\", \"subnet-789\"]\""
    echo "And the format for SECURITY_GROUP_IDS is \"[\"sg-123\", \"sg-456\", \"sg-789\"]\""
    echo "  SUBNET_IDS"
    echo "  SECURITY_GROUP_IDS"
    exit 1
fi

## Change variables as necessary
terraform_solution_path="./deploy"
lambda_runtime="python3.12"
lambda_timeout=300 # number of seconds
lambda_memory=256 # in megabytes
lambda_architecture="x86_64"

## !IMPORTANT! DO NOT MODIFY BELOW THIS LINE
module_name=$(grep '^name' pyproject.toml | sed -e 's/.*"\(.*\)"[\n\r]*/\1/g')
module_description=$(grep '^description' pyproject.toml | sed -e 's/.*"\(.*\)"[\n\r]*/\1/g')
module_version=$(grep '^version' pyproject.toml | sed -e 's/.*"\(.*\)"[\n\r]*/\1/g')
module_export="lambda_function.lambda_handler"

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
echo "Lambda Properties:"
echo "  name: ${module_name}"
echo "  description: ${module_description}"
echo "  runtime: ${lambda_runtime}"
echo "  timeout: ${lambda_timeout}"
echo "  memory: ${lambda_memory}"
echo "  export: ${lambda_export}"

echo
echo "Environment Variables:"
echo "  WORKING_DIR: ${WORKING_DIR}"
echo "  AWS_PROFILE: ${AWS_PROFILE}"
echo "  AWS_REGION: ${AWS_REGION}"
echo "  TERRAFORM_COMMAND: ${TERRAFORM_COMMAND}"
echo "  LAMBDA_ROLE_ARN: ${LAMBDA_ROLE_ARN}"
echo "  DEPLOYMENT_BUCKET_NAME: ${DEPLOYMENT_BUCKET_NAME}"
echo "  LOG_LEVEL: ${LOG_LEVEL}"
echo "  CONNECT_INSTANCE_ID: ${CONNECT_INSTANCE_ID}"
echo "  CONNECT_CONTACT_FLOW_ID: ${CONNECT_CONTACT_FLOW_ID}"
echo "  STREAMING_ENDPOINT_ARN: ${STREAMING_ENDPOINT_ARN}"
echo "  CONNECT_SESSION_DDB_TABLE_NAME: ${CONNECT_SESSION_DDB_TABLE_NAME}"
echo "  CONNECT_SESSION_DDB_TABLE_TTL: ${CONNECT_SESSION_DDB_TABLE_TTL}"
echo "  USER_CHAT_CLIENT_TYPE: ${USER_CHAT_CLIENT_TYPE}"

if [ ! -z "${LAMBDA_LAYER_ARN}" ]; then
    echo "  LAMBDA_LAYER_ARN: ${LAMBDA_LAYER_ARN}"
fi
if [ ! -z "${DEPLOYMENT_BUCKET_PATH}" ]; then
    echo "  DEPLOYMENT_BUCKET_PATH: ${DEPLOYMENT_BUCKET_PATH}"
fi
if [ ! -z "${SUBNET_IDS}" ]; then
    echo "  SUBNET_IDS: ${SUBNET_IDS}"
fi
if [ ! -z "${SECURITY_GROUP_IDS}" ]; then
    echo "  SUBNET_IDS: ${SECURITY_GROUP_IDS}"
fi
echo

## deploy lambda

# create conditional variable values (if any)
lambda_layer_arn=""
if [ ! -z "${LAMBDA_LAYER_ARN}" ]; then
    lambda_layer_arn="${LAMBDA_LAYER_ARN}"
fi
lambda_vpc_subnet_id_list="[]"
if [ ! -z "${SUBNET_IDS}" ]; then
    lambda_vpc_subnet_id_list="${SUBNET_IDS}"
fi
lambda_vpc_sg_id_list="[]"
if [ ! -z "${SECURITY_GROUP_IDS}" ]; then
    lambda_vpc_sg_id_list="${SECURITY_GROUP_IDS}"
fi
lambda_s3_source_bucket_key=""
if [ ! -z "${DEPLOYMENT_BUCKET_PATH}" ]; then
    lambda_s3_source_bucket_key="${DEPLOYMENT_BUCKET_PATH}"
fi

# create a temporary tarraform .tfvars file
cat >/tmp/$$.tfvars <<EOF
region              = "${AWS_REGION}"
lambda_role_arn     = "${LAMBDA_ROLE_ARN}"
lambda_layer_arn = ["${lambda_layer_arn}"]

lambda_vpc_subnet_id_list    = ${lambda_vpc_subnet_id_list}
lambda_vpc_sg_id_list        = ${lambda_vpc_sg_id_list}
lambda_s3_source_bucket_name = "${DEPLOYMENT_BUCKET_NAME}"
lambda_s3_source_bucket_key  = "${lambda_s3_source_bucket_key}"

lambda_function_name        = "${module_name}"
lambda_function_description = "${module_description}"
lambda_function_version     = "${module_version}"
lambda_source_code_path     = "$(pwd)"
lambda_handler              = "${module_export}"
lambda_runtime              = "${lambda_runtime}"
lambda_architecture         = "${lambda_architecture}"
lambda_mem_size             = ${lambda_memory}
lambda_timeout              = ${lambda_timeout}

lambda_environment_variables = {
  "LOG_LEVEL"                      = "${LOG_LEVEL}"
  "CONNECT_INSTANCE_ID"            = "${CONNECT_INSTANCE_ID}"
  "CONNECT_CONTACT_FLOW_ID"        = "${CONNECT_CONTACT_FLOW_ID}"
  "STREAMING_ENDPOINT_ARN"         = "${STREAMING_ENDPOINT_ARN}"
  "CONNECT_SESSION_DDB_TABLE_NAME" = "${CONNECT_SESSION_DDB_TABLE_NAME}"
  "CONNECT_SESSION_DDB_TABLE_TTL"  = "${CONNECT_SESSION_DDB_TABLE_TTL}"
  "USER_CHAT_CLIENT_TYPE"          = "${USER_CHAT_CLIENT_TYPE}"
}
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
