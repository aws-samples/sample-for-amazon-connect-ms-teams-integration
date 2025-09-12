# pylint: disable=import-error,unused-import
# hack to make sure we can import modules in ../src/** modules
try:
    import __setup__
except ModuleNotFoundError:
    import tests.__setup__
# end hack
# pylint: enable=import-error,unused-import

import os
import traceback
import sys
from datetime import datetime
from unittest import IsolatedAsyncioTestCase
from typing import Any, Dict
# from aiohttp import web
from aiohttp.web import Response, json_response
from botbuilder.core import (
    BotFrameworkAdapterSettings,
    TurnContext,
    BotFrameworkAdapter,
)
# from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity, ActivityTypes

# MyBot imports
from botbuilder.core import ActivityHandler
from botbuilder.schema import ChannelAccount

class MyBot(ActivityHandler):
    """
    See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.
    """

    async def on_message_activity(self, turn_context: TurnContext):
        await turn_context.send_activity(f"You said '{ turn_context.activity.text }'")

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")

class TestBotBuilderSdk(IsolatedAsyncioTestCase):
    """TestBotBuilderSdk"""
    ADAPTER: BotFrameworkAdapter = None
    BOT: MyBot = None

    def __init__(self, *args, **kwargs):
        super(TestBotBuilderSdk, self).__init__(*args, **kwargs)

        # load client_id and client_secret from environment variables
        client_id = os.environ.get("TEAMS_APP_CLIENT_ID")
        client_secret = os.environ.get("TEAMS_APP_CLIENT_SECRET")
        channel_auth_tenant = os.environ.get("TEAMS_TENANT_ID", "")
        SETTINGS = BotFrameworkAdapterSettings(client_id, client_secret, channel_auth_tenant=channel_auth_tenant)
        self.ADAPTER = BotFrameworkAdapter(SETTINGS)
        self.BOT = MyBot()

    async def test_bot(self):
        """test_bot"""
        teams_event_payload = {
            "text": "What can you tell me about Amazon?",
            "textFormat": "plain",
            "attachments": [
                {
                    "contentType": "text/html",
                    "content": "<p>What can you tell me about Amazon?</p>"
                }
            ],
            "type": "message",
            "timestamp": "2024-03-16T20:36:43.4785193Z",
            "localTimestamp": "2024-03-16T16:36:43.4785193-04:00",
            "id": "1710621403433",
            "channelId": "msteams",
            "serviceUrl": "https://smba.trafficmanager.net/ca/",
            "from": {
                "id": "29:1dHSuwj-p-abc-abc",
                "name": "Salman Moghal",
                "aadObjectId": "850a5427-f082-41fd-b4a9-2c6db3186d86"
            },
            "conversation": {
                "conversationType": "personal",
                "tenantId": "abc-3a66-4cc3-9b76-abc",
                "id": "a:1q-abc-abc"
            },
            "recipient": {
                "id": "28:abc-9b11-4566-a5e1-abc",
                "name": "connect-bot-1"
            },
            "entities": [
                {
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Mac",
                    "timezone": "America/Toronto",
                    "type": "clientInfo"
                }
            ],
            "channelData": {
                "tenant": {
                    "id": "abc-3a66-4cc3-9b76-abc"
                }
            },
            "locale": "en-US",
            "localTimezone": "America/Toronto"
        }

        auth_header = "Bearer abc.abc.abc-abc-abc-abc-abc"
        response = await self.messages(payload=teams_event_payload, auth_header=auth_header)
        self.assertIsNotNone(response)


    # Catch-all for errors.
    async def on_error(self, context: TurnContext, error: Exception):
        """on_error"""
        # This check writes out errors to console log .vs. app insights.
        # NOTE: In production environment, you should consider logging this to Azure
        #       application insights.
        print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
        traceback.print_exc()

        # Send a message to the user
        await context.send_activity("The bot encountered an error or bug.")
        await context.send_activity(
            "To continue to run this bot, please fix the bot source code."
        )
        # Send a trace activity if we're talking to the Bot Framework Emulator
        if context.activity.channel_id == "emulator":
            # Create a trace activity that contains the error object
            trace_activity = Activity(
                label="TurnError",
                name="on_turn_error Trace",
                timestamp=datetime.utcnow(),
                type=ActivityTypes.trace,
                value=f"{error}",
                value_type="https://www.botframework.com/schemas/error",
            )
            # Send a trace activity, which will be displayed in Bot Framework Emulator
            await context.send_activity(trace_activity)

    # Listen for incoming requests on /api/messages
    async def messages(self, payload: Dict[str, Any], auth_header: str) -> Response:
        """messages"""
        activity = Activity().deserialize(payload)

        try:
            response = await self.ADAPTER.process_activity(activity, auth_header, self.BOT.on_turn)
            if response:
                return json_response(data=response.body, status=response.status)
            return Response(status=201)
        except Exception as exception:
            raise exception
