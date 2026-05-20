
# Overview

This repository contains accompanying source code for the AWS Blog post, [Streamline employee support with Amazon Connect and Microsoft Teams integration](https://aws.amazon.com/blogs/contact-center/streamline-employee-support-with-amazon-connect-and-microsoft-teams-integration/)

This application allows Microsoft Teams to communicate with Amazon Connect via Azure Bot service. As a user, you must launch this application to start a conversation with Amazon Connect.

When a user sends a message in Microsoft Teams, the message is intercepted by Azure Bot service, which invokes Amazon API Gateway. A Lambda function, `connect-api-lambda`, starts a chat session with Amazon Connect and starts a CCP flow execution. This Lambda function stores the necessary Microsoft Teams user metadata and Amazon Connect metadata into an Amazon DynamoDB table. The metadata is later used during the response flow.

The CCP flow contains Amazon Lex chatbot integration. Amazon Lex responds based on the user's input. To keep things simple, for demonstration purposes, the solution uses basic Amazon Lex utterances and canned responses.

Amazon Connect routes the response to an SNS topic when a chat response is generated, either from the CCP flow directly or from a live agent. The SNS subscription triggers another Lambda function, `connect-stream-lambda`. This Lambda function looks up the user's Microsoft Teams metadata in DynamoDB using the contact ID sent in the SNS payload, then sends the Amazon Connect response to the appropriate Teams user via the Microsoft BotBuilder framework.

![Figure 1: Amazon Connect & Microsoft Teams Integration architecture](./docs/ConnectTeamsIntegration.png)

The solution implements a private chat with a Microsoft Teams app. You can extend it to interact with a Teams app that is part of a group conversation.

## Pre-requisites

### Microsoft Teams

You must have an active Microsoft Teams business plan. This allows creation and publishing of a Teams app used to demonstrate the solution.

### Azure resources

The solution requires an Azure Bot that integrates with Microsoft Teams and acts as an interface between Teams and Amazon API Gateway.

Follow the [pre-requisites guide](Prerequisites.md) to set these up. Note the following values — you will need them when configuring `sample.tfvars` before deploying:

1. Teams app client ID — `teams_app_client_id`
2. Teams app client secret — `teams_app_client_secret`
3. Teams app tenant ID — `teams_tenant_id`
4. Whether the app is single tenant — `teams_is_single_tenant_app` (set to `"true"` for single tenant)
5. User chat client type — `user_chat_client_type` (set to `"TEAMS"` for this solution)

### Python virtual environment

The build scripts require a Python 3.12+ virtual environment. Create and activate one before running any build or deploy steps:

```bash
cd chat-clients-sdk
python3.12 -m venv .venv
source .venv/bin/activate
pip install build
```

## Deployment

### Step 1 — Build the Lambda layer

The `chat-clients-sdk` Lambda layer must be built before deploying any Terraform resources.

```bash
cd chat-clients-sdk
source .venv/bin/activate   # if not already active
python -m build
sh build-layer.sh
```

This produces `chat-clients-sdk/build/compressed/chat-clients-sdk-layer-<version>.zip`, which is referenced by the main Terraform deployment.

#### Optional: deploy the layer separately

If you want to publish the layer to AWS independently (for example, to reuse it across multiple deployments), use the provided deploy script:

```bash
cd chat-clients-sdk
export AWS_PROFILE=your-profile
export AWS_REGION=us-east-1
export TERRAFORM_COMMAND=apply
export LAYER_NAME=chat-clients-sdk-layer
export LAYER_DESCRIPTION="Chat clients SDK layer"
export LAYER_RUNTIMES="python3.12"
sh deploy-layer-terraform.sh
```

### Step 2 — Configure deployment variables

Copy `deployment/solution/sample.tfvars` and fill in your values:

```bash
cp deployment/solution/sample.tfvars deployment/solution/my.tfvars
```

At minimum, update the following:

```hcl
aws_region              = "us-east-1"          # your target region
teams_app_client_id     = "YOUR_TEAMS_APP_CLIENT_ID"
teams_app_client_secret = "YOUR_TEAMS_APP_CLIENT_SECRET"
teams_tenant_id         = "YOUR_TEAMS_APP_TENANT_ID"
connect_instance_alias  = "your-unique-alias"  # must be globally unique across all AWS accounts
```

### Step 3 — Deploy with Terraform

```bash
cd deployment/solution
terraform init
terraform apply -var-file="my.tfvars"
```

Terraform will deploy:
- Amazon DynamoDB table (chat session store)
- KMS key (encryption for DynamoDB, Lambda, SNS, CloudWatch)
- `connect-api-lambda` and `connect-stream-lambda` Lambda functions
- Amazon SNS topic and subscription
- Amazon API Gateway REST API (`/teams` and `/web` endpoints)
- Amazon Lex bot with intents
- Amazon Connect instance and contact flow

### Step 4 — Build the Lex bot

Terraform creates the Lex bot and intents but cannot trigger the build. After `terraform apply` completes:

1. Open the [Amazon Lex Console](https://us-east-1.console.aws.amazon.com/lexv2/home)
2. Navigate to the created bot → **Bot versions** → **All languages** → **English (US)**
3. Click **Build**

The bot must be built before Amazon Connect can invoke it.

### Step 5 — Update the Azure Bot messaging endpoint

After Terraform completes, it outputs the API Gateway invoke URL:

```
connect_api_url = "https://<id>.execute-api.<region>.amazonaws.com/dev/teams"
```

Set this as the **Messaging endpoint** in your Azure Bot configuration (Azure Portal → your bot → **Configuration**).

### Step 6 — Publish the bot to Microsoft Teams

1. Edit [`azure-bot/teams-manifest/manifest.json`](./azure-bot/teams-manifest/manifest.json) and update:

    ```plaintext
    id:                      A valid UUID (generate one at https://www.uuidgenerator.net/)
    developer.websiteUrl:    https:// URL to your company or product landing page
    developer.privacyUrl:    https:// URL to your privacy policy
    developer.termsOfUseUrl: https:// URL to your terms of use
    bots.botId:              Your Azure Bot App ID
    ```

    Refer to the [Teams Manifest Schema guidelines](https://learn.microsoft.com/en-us/microsoftteams/platform/resources/schema/manifest-schema) for full details.

2. Compress the **contents** inside the `azure-bot/teams-manifest/` folder into a zip file.

3. Visit the [Teams Developer Portal](https://dev.teams.microsoft.com/tools) and select **Import an app**. Upload the zip to create the app.

    ![Import App](./docs/images/import_app.png)

4. Open the app settings, go to **Publish** → **Publish to org**, and click **Publish your app**.

    ![Publish](./docs/images/publish_app.png) ![Publish to Org](./docs/images/publish_app_to_org.png)

## Testing

Open the published Teams app and start a conversation with the bot. Try phrases like:

- `"Can you help me reset my password"` — triggers the `ResetPassword` intent
- `"What is the status of the ticket?"` — triggers the `TicketStatus` intent
- `"I want to speak with an agent"` — triggers the `TalkToAgent` intent and routes to a live queue

Canned responses are returned by default. These can be enhanced in Amazon Lex by adding Lambda fulfillment hooks to execute custom business logic.

To test live agent chat, follow the [Amazon Connect chat testing guide](https://docs.aws.amazon.com/connect/latest/adminguide/chat-testing.html#test-chat).

## Clean-up

### AWS resources

```bash
cd deployment/solution
terraform destroy -var-file="my.tfvars"
```

### Azure resources

1. In the Azure Portal, open your Azure Bot → **Overview** → **Delete**.

    ![DeleteBot](./docs/images/delete_bot.png)

2. Open **App registrations**, find your registration, and click **Delete**.

    ![app_registration](./docs/images/app_registration.png)

    ![DeleteRegistration](./docs/images/delete_app_registration.png)
