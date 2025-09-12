
import os
import asyncio
from typing import Any
from typing import Dict
from logging import Logger
from datetime import datetime
from botbuilder.core import (
    BotFrameworkAdapterSettings,
    TurnContext,
    BotFrameworkAdapter,
    ActivityHandler
)
from botbuilder.schema import Activity, ActivityTypes
from chat_clients.common.logging_helper import get_logger
from chat_clients.teams.echo_bot import EchoBot


class TeamsClient:
    """TeamsClient"""
    # class variables
    auth_header: str = None
    is_single_tenant: bool = True
    app_client_id: str = None
    app_client_secret: str = None
    channel_auth_tenant: str = None
    client_adapter: BotFrameworkAdapter = None
    bot: ActivityHandler = None

    # logger
    logger: Logger = None

    def __init__(self, auth_header: str, bot: ActivityHandler = None):
        # initialize super class
        super().__init__()

        # configure logger
        self.logger = get_logger(f"{__name__}.{type(self).__name__}")

        # set class variables
        self.auth_header = auth_header

        # initialize environment variables
        self.__init_env()

        # initialize the bot
        if self.is_single_tenant:
            bot_settings = BotFrameworkAdapterSettings(self.app_client_id, self.app_client_secret, channel_auth_tenant=self.channel_auth_tenant)
        else:
            bot_settings = BotFrameworkAdapterSettings(self.app_client_id, self.app_client_secret)

        self.client_adapter = BotFrameworkAdapter(bot_settings)
        self.client_adapter.on_turn_error = self.__on_error
        self.bot = bot if bot else EchoBot()

    def __init_env(self) -> None:
        """
        Read values from environment variables
        """
        self.is_single_tenant = os.environ.get("TEAMS_IS_SINGLE_TENANT_APP", "true").lower() == "true"
        self.app_client_id = os.environ.get("TEAMS_APP_CLIENT_ID", None)
        self.app_client_secret = os.environ.get("TEAMS_APP_CLIENT_SECRET", None)
        self.channel_auth_tenant = os.environ.get("TEAMS_TENANT_ID", None)

    # Catch-all for errors.
    async def __on_error(self, context: TurnContext, error: Exception):
        """on_error"""
        # This check writes out errors to console log .vs. app insights.
        # NOTE: In production environment, you should consider logging this to Azure
        #       application insights.
        self.logger.error("\n [on_turn_error] unhandled error: %s", error)

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
                timestamp=datetime.now(),
                type=ActivityTypes.trace,
                value=f"{error}",
                value_type="https://www.botframework.com/schemas/error",
            )
            # Send a trace activity, which will be displayed in Bot Framework Emulator
            await context.send_activity(trace_activity)

    async def __send_messages(self, activity: Dict[str, Any]) -> Dict:
        """
        This method uses MS BotBuilder framework to send a message to
        MS Teams.  BotFrameworkAdapter.process_activity() takes `ActivityHandler`,
        or Bot, as an input parameter.  The activity handler class must implement
        `on_*_activity` methods that MS BotBuilder framework invokes to process
        the incoming message from MS Teams.  For example, to send a reply to
        MS Teams conversation, use TurnContext.send_activity to send a plan text
        or adaptive card message.  Refer to `echo_bot.py` for more details.

        Args:
            activity (Dict[str, Any]): _description_

        Returns:
            Dict: _description_
        """
        activity = Activity().deserialize(activity)

        try:
            response = await self.client_adapter.process_activity(activity, self.auth_header, self.bot.on_turn)
            if response:
                return {
                    "data": response.body,
                    "status": response.status,
                }
            return { "status": 201 }
        except Exception as exception:
            self.logger.error("Error occurred while calling BotFrameworkAdapter.process_activity(): %s", exception)
            return { "status": 500 }

    def process_activity(self, activity: Dict[str, Any]) -> Dict:
        """Process activity from teams client

        Args:
            activity (Dict[str, Any]): teams activity payload

        Returns:
            Dict: Response from teams client
        """
        self.logger.debug("Initiating asyncio loop")
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.__send_messages(activity=activity))
        self.logger.debug("response: %s", response)
        return response
