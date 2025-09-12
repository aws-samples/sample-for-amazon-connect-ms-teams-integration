"""teams_bot.py - module contains Teams bot that handles Amazon Connect response"""

from logging import Logger
from chat_clients.common.logging_helper import get_logger
from botbuilder.core import ActivityHandler, TurnContext

ERROR_MESSAGE = "Sorry, something went wrong while processing your request.  Please try again."

class TeamsBot(ActivityHandler):
    """
    This bot handles sends Amazon Connect response to the user.
    """
    # class variables
    message: str = None

    # logger
    logger: Logger = None

    def __init__(self, message: str):
        super().__init__()

        # configure logger
        self.logger = get_logger(f"{__name__}.{type(self).__name__}")

        # initialize class variables
        self.message = message

    async def on_message_activity(self, turn_context: TurnContext):
        # if message is not set, return
        if not self.message or len(self.message) <= 0:
            self.logger.debug("Amazon Connect response is empty.  Returning error response: %s  Turn context activity: %s", ERROR_MESSAGE, str(turn_context.activity))
            await turn_context.send_activity(ERROR_MESSAGE)
            return

        await turn_context.send_activity(self.message)
