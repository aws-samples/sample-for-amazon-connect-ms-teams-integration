# Enabling Amazon Q in Connect AI Agent

This guide walks through adding Amazon Q in Connect AI Agent capability to an
existing deployment of the Amazon Connect + Microsoft Teams integration. The
changes are fully backward compatible — your existing Lex intents and contact
flow continue to work unchanged.

## What this adds

Without the AI Agent, unrecognised utterances loop back to "How can I help you
today?". With the AI Agent, those same utterances are answered by a generative
AI model backed by a knowledge base you configure (web crawler, S3 documents,
Salesforce, ServiceNow, etc.).

```plaintext
Before:  User message → Lex → no intent match → re-prompt
After:   User message → Lex → no intent match → Q in Connect AI Agent → answer
```

Your existing intents (`ResetPassword`, `TalkToAgent`, etc.) are unaffected.

---

## Prerequisites

- The base solution is deployed and working end-to-end (Teams → Connect → Lex → Teams)
- You have AWS CLI access to the account and region where Connect is deployed
- You have Admin access to the Amazon Connect dashboard
- Your Connect instance was created after December 2025, **or** you have enabled
  `MESSAGE_STREAMING` manually (see Step 1)

---

## Step 1 — Verify MESSAGE_STREAMING is enabled

AI Agent responses are delivered as streaming chunks via SNS. Without this
setting, responses are silently dropped and never reach the user.

Run the following, substituting your instance ID and region:

```bash
aws connect describe-instance-attribute \
  --instance-id YOUR_INSTANCE_ID \
  --attribute-type MESSAGE_STREAMING \
  --region YOUR_REGION
```

If the output shows `"Value": "true"`, skip to Step 2.

If the output shows `"Value": "false"` or the attribute is missing, enable it:

```bash
aws connect update-instance-attribute \
  --instance-id YOUR_INSTANCE_ID \
  --attribute-type MESSAGE_STREAMING \
  --value true \
  --region YOUR_REGION
```

> Instances created after December 2025 have this enabled by default.

---

## Step 2 — Enable Amazon Q in Connect for your instance

1. Open the [Amazon Connect console](https://console.aws.amazon.com/connect/home)
2. Click on your instance name
3. In the left navigation, click **Amazon Q**
4. Click **Enable Amazon Q in Connect**
5. Follow the prompts to enable it

If you already see an **Amazon Q** section with options, it is already enabled.

---

## Step 3 — Create a knowledge base

The AI Agent answers questions by searching a knowledge base. You need to create
one and connect it to a data source.

1. In the Amazon Connect console, go to **Amazon Q** → **Knowledge bases**
2. Click **Create knowledge base**
3. Give it a name (e.g. `service-desk-kb`)
4. Under **Data source**, choose the type that matches your content:
   - **Web crawler** — crawls a website URL you specify
   - **Amazon S3** — indexes documents stored in an S3 bucket
   - **Salesforce / ServiceNow** — connects to your ticketing system
5. Configure the data source:
   - For **Web crawler**: enter the starting URL(s) to crawl, set crawl depth
   - For **S3**: select the bucket and prefix containing your documents
6. Under **Embeddings model**, select an Amazon Bedrock model
   (e.g. `Amazon Titan Embeddings V2`)
7. Click **Create knowledge base**
8. Wait for the initial sync to complete (this can take several minutes to hours
   depending on the size of your content)

> Note the **Knowledge base ARN** — you will need it in Step 4.

---

## Step 4 — Create an AI Agent application

1. In the Amazon Connect console, go to **Amazon Q** → **AI agents**
2. Click **Create AI agent**
3. Choose type: **Self-service**
4. Give it a name (e.g. `service-desk-ai-agent`)
5. Under **Knowledge base**, select the knowledge base you created in Step 3
6. Under **AI prompt** (optional), customise the system instructions. Example:

   ```plaintext
   You are a helpful IT service desk assistant. Help employees with common IT
   issues including password resets, software access, and connectivity problems.

   Use the knowledge base to answer questions accurately.
   When the customer wants to speak to a human agent, use the ESCALATION tool.
   When the customer's issue is resolved, use the COMPLETE tool.
   ```

7. Click **Create**
8. Note the **Assistant ARN** from the details page — it looks like:
   `arn:aws:wisdom:REGION:ACCOUNT:assistant/ASSISTANT-ID`

---

## Step 5 — Add AMAZON.QinConnectIntent to the Lex bot

This built-in intent activates the AI Agent for utterances that don't match
your custom intents.

1. Open the [Amazon Lex console](https://console.aws.amazon.com/lexv2/home)
2. Click on your bot (e.g. `connect_integration_lex_bot`)
3. In the left panel, click **Bot versions** → **Draft version**
4. Click **All languages** → **English (US)**
5. Click **Intents** in the left panel
6. Click **Add intent** → **Use built-in intent**
7. Select `AMAZON.QinConnectIntent` from the list and click **Add**
8. On the intent configuration page:
   - Under **Amazon Q in Connect Configuration**, paste the **Assistant ARN**
     from Step 4
   - The ARN format is:
     `arn:aws:wisdom:REGION:ACCOUNT:assistant/ASSISTANT-ID`
9. Click **Save intent**

---

## Step 6 — Add wisdom: permissions to the Lex bot IAM role

The Lex bot uses a custom IAM role. When using `AMAZON.QinConnectIntent`, that
role needs permission to call the Q in Connect (Wisdom) APIs. Without this, the
AI Agent is invoked but returns nothing silently.

Find your Lex bot role name — it was set in `my.tfvars` as `lex_bot_iam_role_name`
(e.g. `connect_integration_lex_bot_iam_role`).

Run the following, substituting your values:

```bash
aws iam put-role-policy \
  --role-name YOUR_LEX_BOT_ROLE_NAME \
  --policy-name QInConnectPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "QInConnectAssistantPolicy",
        "Effect": "Allow",
        "Action": [
          "wisdom:CreateSession",
          "wisdom:GetAssistant"
        ],
        "Resource": [
          "YOUR_ASSISTANT_ARN",
          "YOUR_ASSISTANT_ARN/*"
        ]
      },
      {
        "Sid": "QInConnectSessionsPolicy",
        "Effect": "Allow",
        "Action": [
          "wisdom:SendMessage",
          "wisdom:GetNextMessage"
        ],
        "Resource": "arn:aws:wisdom:YOUR_REGION:YOUR_ACCOUNT:session/YOUR_ASSISTANT_ID/*"
      }
    ]
  }'
```

Replace:

- `YOUR_LEX_BOT_ROLE_NAME` — the IAM role name from `my.tfvars`
- `YOUR_ASSISTANT_ARN` — the full ARN from Step 4
- `YOUR_REGION` — e.g. `ap-southeast-2`
- `YOUR_ACCOUNT` — your 12-digit AWS account ID
- `YOUR_ASSISTANT_ID` — the UUID portion of the assistant ARN

---

## Step 7 — Add lex:RecognizeMessageAsync to the Lex bot alias policy

The AI Agent uses an asynchronous Lex API (`lex:RecognizeMessageAsync`) in
addition to the standard `lex:RecognizeText`. This permission must be added to
the bot alias resource-based policy.

First, get your bot ID and alias ID:

```bash
# Get bot ID
aws lexv2-models list-bots \
  --region YOUR_REGION \
  --query "botSummaries[?botName=='connect_integration_lex_bot'].botId" \
  --output text

# Get alias ID (TestBotAlias)
aws lexv2-models list-bot-aliases \
  --bot-id YOUR_BOT_ID \
  --region YOUR_REGION \
  --query "botAliasSummaries[?botAliasName=='TestBotAlias'].botAliasId" \
  --output text
```

Then check if a policy already exists:

```bash
aws lexv2-models describe-resource-policy \
  --resource-arn arn:aws:lex:YOUR_REGION:YOUR_ACCOUNT:bot-alias/YOUR_BOT_ID/YOUR_ALIAS_ID \
  --region YOUR_REGION 2>/dev/null
```

**If no policy exists**, create one:

```bash
aws lexv2-models create-resource-policy \
  --resource-arn arn:aws:lex:YOUR_REGION:YOUR_ACCOUNT:bot-alias/YOUR_BOT_ID/YOUR_ALIAS_ID \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "connect-ai-agent",
      "Effect": "Allow",
      "Principal": {"Service": "connect.amazonaws.com"},
      "Action": [
        "lex:RecognizeMessageAsync",
        "lex:RecognizeText",
        "lex:StartConversation"
      ],
      "Resource": "arn:aws:lex:YOUR_REGION:YOUR_ACCOUNT:bot-alias/YOUR_BOT_ID/YOUR_ALIAS_ID",
      "Condition": {
        "StringEquals": {"AWS:SourceAccount": "YOUR_ACCOUNT"},
        "ArnEquals": {
          "AWS:SourceArn": "arn:aws:connect:YOUR_REGION:YOUR_ACCOUNT:instance/YOUR_INSTANCE_ID"
        }
      }
    }]
  }' \
  --region YOUR_REGION
```

**If a policy already exists**, update it (replace the existing policy):

```bash
aws lexv2-models update-resource-policy \
  --resource-arn arn:aws:lex:YOUR_REGION:YOUR_ACCOUNT:bot-alias/YOUR_BOT_ID/YOUR_ALIAS_ID \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "connect-ai-agent",
      "Effect": "Allow",
      "Principal": {"Service": "connect.amazonaws.com"},
      "Action": [
        "lex:RecognizeMessageAsync",
        "lex:RecognizeText",
        "lex:StartConversation"
      ],
      "Resource": "arn:aws:lex:YOUR_REGION:YOUR_ACCOUNT:bot-alias/YOUR_BOT_ID/YOUR_ALIAS_ID",
      "Condition": {
        "StringEquals": {"AWS:SourceAccount": "YOUR_ACCOUNT"},
        "ArnEquals": {
          "AWS:SourceArn": "arn:aws:connect:YOUR_REGION:YOUR_ACCOUNT:instance/YOUR_INSTANCE_ID"
        }
      }
    }]
  }' \
  --region YOUR_REGION
```

---

## Step 8 — Build the Lex bot

After adding `AMAZON.QinConnectIntent`, the bot must be rebuilt before the
changes take effect. **This step is required every time you change intents or
utterances.**

1. In the Lex console, open your bot
2. Go to **Draft version** → **All languages** → **English (US)**
3. Click **Build**
4. Wait for the status to change from **Building** to **Built** (typically 1–2 minutes)

> If you skip this step, the new intent will not be active and all unrecognised
> utterances will loop back to the Lex prompt instead of reaching the AI Agent.

---

## Step 9 — Update the contact flow

The contact flow needs a **Connect assistant** block to associate the AI Agent
with the contact before the Lex invocation. Without this block, the
`AMAZON.QinConnectIntent` fires but has no session context and cannot respond.

### 9a — Open the flow

1. In the Amazon Connect console, go to **Routing** → **Flows**
2. Click on `teams-integration-connect-flow`
3. The flow designer opens

### 9b — Add the Connect assistant block

1. In the block palette on the left, search for **Connect assistant**
   (it is under the **Integrate** category)
2. Drag the **Connect assistant** block onto the canvas, placing it between
   the **Check contact attributes** block and the **lex invoke block**

### 9c — Configure the Connect assistant block

1. Click on the **Connect assistant** block to open its settings
2. Under **Select an assistant**, choose the AI agent you created in Step 4
3. Click **Save**

### 9d — Rewire the connections

The **Check contact attributes** block currently has three outputs:
`= CHAT`, `= VOICE`, and `No Match`. You need to route the chat path through
the Connect assistant block.

**Delete the existing `= CHAT` connection:**

1. Hover over the arrow from `= CHAT` to the **lex invoke block**
2. Click the arrow to select it (it highlights)
3. Press **Delete**

**Delete the existing `No Match` connection:**

1. Hover over the arrow from `No Match` to the **lex invoke block**
2. Click to select, press **Delete**

**Wire `= CHAT` → Connect assistant:**

1. Hover over the **Check contact attributes** block
2. A small circle appears on the right edge of the `= CHAT` row
3. Click and drag from that circle to the **Connect assistant** block
4. Release when the Connect assistant block highlights blue

**Wire `No Match` → Connect assistant:**

1. Same as above but from the `No Match` row
2. Drag to the same **Connect assistant** block

**Wire Connect assistant `Success` → lex invoke block:**

1. Hover over the **Connect assistant** block
2. Drag from the **Success** output circle to the **lex invoke block**

**Wire Connect assistant `Error` → lex invoke block:**

1. Drag from the **Error** output circle to the **lex invoke block**
2. This is the fallback — if the assistant association fails, the flow
   continues to Lex directly

The `= VOICE` connection remains unchanged — it still goes to the voice
greeting message block.

### 9e — Save and publish

1. Click **Save** in the top right corner
2. Click **Publish**
3. Confirm the publish dialog

---

## Step 10 — Redeploy the Lambda layer

The `StartChatContact` API call needs `SupportedMessagingContentTypes` to
include interactive message types used by the AI Agent. This change is already
in the codebase (`chat-clients-sdk/src/chat_clients/connect/client.py`).

Rebuild and redeploy:

```bash
cd chat-clients-sdk
source .venv/bin/activate
python -m build
sh build-layer.sh

cd ../deployment/solution
terraform apply -var-file="my.tfvars"
```

> If you are on the original version of the code (before this fix was applied),
> check that `StartChatContact` in `client.py` includes the
> `SupportedMessagingContentTypes` parameter. If it does not, pull the latest
> version of the code before rebuilding.

---

## Step 11 — Test

Open the Teams app and start a new conversation. Send a message that your
knowledge base content would answer — something outside the custom intents.

**Expected flow:**

```plaintext
User:   Hi
Bot:    Please give me a few moments to process your request.
Bot:    How can I help you today?

User:   I can't access my work email from home
Bot:    Please give me a few moments to process your request.
Bot:    [AI Agent response based on your knowledge base content]

User:   Can you help me reset my password?
Bot:    Please give me a few moments to process your request.
Bot:    Ok, let me initiate a password reset    ← custom Lex intent still works
```

---

## Troubleshooting

### Nothing comes back after the user's message

Check the Connect flow logs in CloudWatch:

```bash
aws logs filter-log-events \
  --log-group-name /aws/connect/YOUR_INSTANCE_ID \
  --start-time $(date -v-30M +%s)000 \
  --region YOUR_REGION \
  --query 'events[*].message' \
  --output text 2>/dev/null || \
aws logs filter-log-events \
  --log-group-name /aws/connect/YOUR_INSTANCE_ID \
  --start-time $(date -d '30 minutes ago' +%s)000 \
  --region YOUR_REGION \
  --query 'events[*].message' \
  --output text
```

Look for a `SetWisdomAssistant` entry. If it is present, the Connect assistant
block ran. If it is absent, the flow is not reaching the Connect assistant block
— check the wiring in Step 9.

If `SetWisdomAssistant` is present but no response arrives, the most likely
cause is missing `wisdom:` permissions on the Lex bot role (Step 6).

### "How can I help you today?" repeats instead of an AI response

The Lex bot was not rebuilt after adding `AMAZON.QinConnectIntent`. Go to the
Lex console and rebuild (Step 8).

### Custom intents (ResetPassword, TalkToAgent, etc.) stopped working

The `AMAZON.QinConnectIntent` only activates for utterances that do not match
any other intent. If custom intents are not matching, the Lex bot may need to
be rebuilt (Step 8), or the utterances in `my.tfvars` may need to be updated
and redeployed.

### AI Agent responds but the response is empty or generic

The knowledge base may not have finished syncing, or the content may not be
relevant to the question asked. In the Connect console, go to **Amazon Q** →
**Knowledge bases** → your knowledge base → check the sync status and review
the indexed content.

### "We're sorry, an error occurred. Goodbye." appears

The Connect assistant block's `Error` output is not wired to the lex invoke
block. Check the flow wiring in Step 9d.

---

## Summary of changes made

| What | Where | Why |
| --- | --- | --- |
| `MESSAGE_STREAMING` enabled | Connect instance attribute | Required for AI Agent streaming responses via SNS |
| `AMAZON.QinConnectIntent` added | Lex bot | Activates AI Agent for unrecognised utterances |
| `wisdom:` permissions added | Lex bot IAM role | Required for Lex to call Q in Connect APIs |
| `lex:RecognizeMessageAsync` added | Lex bot alias policy | Required for async AI Agent invocation |
| Lex bot rebuilt | Lex console | Activates the new intent |
| Connect assistant block added | Contact flow | Associates AI Agent session with the contact |
| `SupportedMessagingContentTypes` | `client.py` / Lambda layer | Enables interactive message types from AI Agent |
