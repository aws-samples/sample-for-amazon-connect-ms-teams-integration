# Overview

## Sign up with Microsoft 365 Essentials

1. Go to [Microsoft Teams Business Plans](https://www.microsoft.com/en-ca/microsoft-teams/compare-microsoft-teams-business-options?activetab=pivot:primaryr1)

2. Sign up on “Microsoft Teams Essentials” (try one month for free)

### Once you are signed-up, you will be able to sign into these sites:

- [Microsoft 365 admin center](https://admin.microsoft.com/#/homepage)

- [Azure Portal](https://portal.azure.com/#home)

- [Teams Developer Portal](https://dev.teams.microsoft.com/home)

## Creating the Azure Bot

1. Login to the [Azure Portal](https://portal.azure.com/#home)
2. Click on "Create a resource" to create a new Azure Bot.

    ![Create bot](./docs/images/createBotPage.png)

3. Click on "Azure Bot" to begin creating the bot.

    ![Azure Bot](./docs/images/azureBot.png)

4. Give the bot a unique name for the Bot handle. This name needs to be globally unique. You can set a different display name later. Note: Try to keep the Bot Handle less than 20 characters. Choose a subscription if you have multiple subscriptions available. Click "Create new" to make a new resource group for the bot.

    ![botPage](./docs/images/botPage.png)

5. Give the resource group a unique name. It's best practice to start the resource group name with "rg-".

    ![rgBot](./docs/images/rgBot.png)

6. Select a location for the new resource group. For this example, "Canada Central" is used. Select "Single Tenant" as the App type. Choose "Create new Microsoft App ID" for the Creation type. Click "Review + Create".

    ![botReview](./docs/images/botReview.png)

7. Click "Create" to deploy the Azure Bot.

    ![finalBotPage](./docs/images/finalBotPage.png)

> **Note on App Registration:** Selecting "Create new Microsoft App ID" automatically creates an Entra ID App Registration for the bot. This registration provides the `client_id` and `client_secret` used by the BotFramework SDK to authenticate requests between Azure Bot Service and the Lambda. This is the only registration required for this solution.

> **Optional — SSO user identity verification:** If you want to verify the identity of the Teams user in the Lambda (for example, to look them up in an HR system or restrict access by role), you would create a second, separate App Registration with a custom scope (e.g. `GenAI.chatbot.proxy.read`) and implement a [Teams SSO token validation](https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/authentication/bot-sso-overview) step in the Lambda. This solution does not implement SSO validation, so the second registration is not needed.

## (Optional) Create a Microsoft Entra ID for SSO user identity validation in Lambda

> **This step is optional.** The bot works without it. Create this registration only if you intend to implement SSO token validation in the Lambda — for example, to verify the Teams user's identity, look them up in a directory, or restrict access by role. The current solution does not use this registration.

This registration acts as the audience for the JWT that Teams generates via SSO, and defines the permission scope the Lambda can request.

1. In the Azure Portal, navigate to **Microsoft Entra ID**.

    ![entraId](./docs/images/entraId.png)

2. Go to **App registrations** and select **New registration**. Enter a unique name and click **Register**.

    ![appId](./docs/images/appId.png)

    ![registerApp](./docs/images/registerApp.png)

3. Navigate to **Expose an API**, click **Add** next to Application ID URL. The URL will populate by default — click **Save**.

    ![exposeAPI](./docs/images/exposeAPI.png)

    ![exposeAPI1](./docs/images/exposeAPI1.png)

4. Click **Add a scope**. The scope name used in this solution is `GenAI.chatbot.proxy.read`. Select **Admins and users** for who can consent, fill in the required fields, and save.

    ![scopeApp](./docs/images/scopeApp.png)

Once created, you would reference this registration's Application ID as the `aud` (audience) claim when validating the Teams SSO token in the Lambda. See the [Microsoft Teams SSO documentation](https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/authentication/bot-sso-overview) for implementation details.

## Steps to Configure Azure Bot

1. Once the Bot is created, navigate to the bot, and open the bot.

    ![botPage1](./docs/images/botPage1.png)

2. Navigate to “Channels” and add “Microsoft Teams” as a Channel from the Available Channels.

    ![channelBot](./docs/images/channelBot.png)

    ![teamsPage](./docs/images/teamsPage.png)

    ![teamsPage1](./docs/images/teamsPage1.png)

3. Navigate to Configuration.
Note: After we deploy our Node JS Messaging API resources using Terraform, we will enter our messaging endpoint here in the configuration. For now, leave this field empty.

    ![configPage](./docs/images/configPage.png)

4. Now click on “Manage Password”, to manage Additional settings for the bot.

    ![pwdPage](./docs/images/pwdPage.png)

Note the following details from the deployed resources:

1. Teams app client ID
2. Teams app client secret
3. Teams app tenant ID

Next, proceed to [README.md](./README.md) for further steps. Once the Terraform resources have been deployed, revisit
the Azure bot and update the **Messaging endpoint** section to the Invoke URL of the API gateway. It would look something like this:

```plaintext
https://abcd1234.execute-api.us-east-1.amazonaws.com/dev/teams
```
