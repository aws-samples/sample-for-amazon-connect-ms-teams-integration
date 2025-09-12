#!/bin/sh

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

## initialize and do some pre-flight checks
if [ -z "$AWS_PROFILE" -o \
    -z "$AWS_REGION" -o \
    -z "$TERRAFORM_COMMAND" -o \
    -z "$LAYER_NAME" -o \
    -z "$LAYER_DESCRIPTION" -o \
    -z "$LAYER_RUNTIMES" ]; then
    echo "Missing environment variables.  Ensure following environment variables are set"
    echo "  AWS_PROFILE"
    echo "  AWS_REGION"
    echo "  TERRAFORM_COMMAND"
    echo "  LAYER_NAME"
    echo "  LAYER_DESCRIPTION"
    echo "  LAYER_RUNTIMES"
    rm -rf /tmp/$$.*
    exit 1
fi

## Change variables as necessary
terraform_solution_path="./deploy"

## !IMPORTANT! DO NOT MODIFY BELOW THIS LINE
layer_name="${LAYER_NAME}"
layer_description="${LAYER_DESCRIPTION}"
layer_runtimes="${LAYER_RUNTIMES}" # white space separated list of runtimes
layer_architecture="x86_64" # white space separated list of architectures.  currently only supports x86_64, arm64 is not tested
project_version=$(grep '^version' pyproject.toml | sed -e 's/.*"\(.*\)"[\n\r]*/\1/g')
layer_version="${project_version}"
layer_description="${layer_description}: version ${project_version}"

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
echo "Layer Properties:"
echo "  Layer name: ${layer_name}"
echo "  Layer version: ${layer_version}"
echo "  Layer description: ${layer_description}"
echo "  Layer compatible runtimes: ${layer_runtimes}"
echo "  Layer compatible architectures: ${layer_architecture}"

echo
echo "Environment Variables:"
echo "  WORKING_DIR: ${WORKING_DIR}"
echo "  AWS_PROFILE: ${AWS_PROFILE}"
echo "  AWS_REGION: ${AWS_REGION}"
echo "  TERRAFORM_COMMAND: ${TERRAFORM_COMMAND}"

## deploy lambda layer

# layer path variables
layer_build="build"
layer_zip="${layer_build}/compressed"

# get module fully qualified path and file name
dist_name_zip="${layer_name}-${layer_version}.zip"
layer_zip_path=$(ls ${layer_zip}/${dist_name_zip})

# check that layer exist
if [ ! -f "${layer_zip_path}" ]; then
    echo "Error: Unable to locate layer distribution zip file: ${layer_zip_path}"
    echo "       Run 'build-layer.sh' script first"
    rm -rf /tmp/$$.*
    exit 1
fi

# create terraform formatted list of layer runtimes
runtimes=$(echo ${layer_runtimes} | sed -e 's/ /","/g' | sed -e 's/^\(.*\)/"\1/g' | sed -e 's/\(.*\)$/\1"/g')
architecture=$(echo ${layer_architecture} | sed -e 's/ /","/g' | sed -e 's/^\(.*\)/"\1/g' | sed -e 's/\(.*\)$/\1"/g')

# create a temporary tarraform .tfvars file
cat >/tmp/$$.tfvars <<EOF
region = "${AWS_REGION}"
this_layer_name = "${layer_name}"
this_layer_description = "${layer_description}"
this_layer_source_code_file_path = "${WORKING_DIR}/${layer_zip_path}"
this_layer_runtimes = [${runtimes}]
this_layer_compatible_arch = [${architecture}]
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
    terraform ${TERRAFORM_COMMAND} -var-file=/tmp/$$.tfvars -auto-approve;
) > /tmp/$$.terraform.log 2>&1
if [ $? -ne 0 ]; then
    echo "Error: Unable to deploy layer"
    cat /tmp/$$.terraform.log
    rm -rf /tmp/$$.*
    exit 1
fi

## clean up
cat /tmp/$$.terraform.log
rm -rf /tmp/$$.*
echo
echo "done!"
