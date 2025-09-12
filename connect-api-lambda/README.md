# Overview

This project contains python code for API lambda.  Workflow is shown in architecture diagram.  Note that this implementation demonstrates how to leverage Chat Clients SDK to interact with Amazon Connect.

## Prereq

Launch the `devcontainer`.  Once the container launches, hit the "+" (New Terminal) icon to start a `bash` terminal.  Make sure to launch the `bash` terminal in `connect-api-lambda` project.  Also double check that VS Code automatically `sources` the `.venv` python virtual environment for this project.

**IMPORTANT**:  If VS Code doesn't automatically source the `.venv` project level python virtual environment, then you did not complete the workspace setup process.  Refer to the [Prerequisites.md](../Prerequisites.md) for more details.

## Setup

Optionally run following command on the `bash` prompt inside `devcontainer` to setup the python project from command line.

Note that this setup is already done when you first launch the `devcontainer` or when you select `Dev Containers: Reopen in Container` option.

```sh
pwd
# make sure you are in 'connect-api-lambda' folder
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lambda Environment Variables

Lambda relies on several environment variables.  During unit test phase, these environment variables are defined in [launch.json](.vscode/launch.json) file.

Additionally, these environment variables are defined in deployment tasks discussed in next section.

> IMPORTANT: `AWS_PROFILE` and `AWS_REGION` are required for unit testing and deployment process execution.  All variable are necessary to instruct Chat Clients SDK execution.

```sh
# required
AWS_PROFILE="YOUR_AWS_PROFILE_NAME" # refers to your AWS profile you created when setting up AWS cli.
AWS_REGION="YOUR_AWS_REGION" # us-east-1 for example
LOG_LEVEL="debug"
CONNECT_INSTANCE_ID="a1234567-aaaa-bbbb-cccc-abcdef123456"
CONNECT_CONTACT_FLOW_ID="b1234567-aaaa-bbbb-cccc-123456abcdef"
STREAMING_ENDPOINT_ARN="arn:aws:sns:us-west-2:1234567890:CONNECT_STREAM" # set to SNS ARN
CONNECT_SESSION_DDB_TABLE_NAME="connect-session-table"
CONNECT_SESSION_DDB_TABLE_TTL="3600" # 1 hour in seconds
TEAMS_IS_SINGLE_TENANT_APP="false" # specify if azure bot (specified by client id below) is single or multi tenant Azure App
# "TEAMS_TENANT_ID="YOUR_AZURE_TENANT_ID" # if single tenant, specify tenant id.  otherwise, leave it blank
TEAMS_APP_CLIENT_ID="YOUR_AZURE_BOT_CLIENT_ID"
TEAMS_APP_CLIENT_SECRET="YOUR_AZURE_BOT_CLIENT_SECRET"
USER_CHAT_CLIENT_TYPE="TEAMS" # set to 'TEAMS', 'SLACK' or 'WEB'
```

## Deployment

Preferred way to deploy this lambda during development is by using terraform script.

The project contains two VS Code Tasks to `deploy` (or update) and `undeploy` Lambda function.  Use VS Code Task `Cmd` + `Shift` + `P` + `Tasks: Run Task` (on Mac) or `Ctrl` + `Shift` + `P` + `Tasks: Run Task` (on Windows) to launch tasks accordingly:

- `connect-api-lambda:terraform:deploy`
- `connect-api-lambda:terraform:undeploy`

Alternatively, run the [terraform deployment](../deployment/solution/) script from solutions folder to deploy this Lambda.

## Lambda Execution Role Requirement

When executing unit tests, ensure that a Lambda Role exists with policies discussed below.  A role with similar policies is required when Lambda function is deployed to AWS account.

Following AWS managed permission are enough for this CloudWatch log read/write access:

- `AWSLambdaBasicExecutionRole`

The role and policies are created during deployment (in section above)

Amazon Connect:

```json
// TBD
```
