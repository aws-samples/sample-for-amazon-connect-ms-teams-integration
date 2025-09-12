"""teams.py - module contains classes that interact with Amazon Connect and Teams"""

from typing import Dict
from logging import Logger
from chat_clients.common.logging_helper import get_logger
from chat_clients.teams.client import TeamsClient as TeamsChatClient
from teams.teams_bot import TeamsBot

class TeamsClient:
    """
    This class uses the TeamsChatClient class to interact with Teams.  It also
    interacts with DynamoDB and Amazon Connect.
    """
    # class constants
    AGENT_DISCONNECT_MESSAGE = "The agent has disconnected."
    AGENT_DISCONNECT_MESSAGE_REPLY = AGENT_DISCONNECT_MESSAGE + " If you need more help, please type your question."

    # class variables
    logger: Logger = None

    def __init__(self):
        """
        Initialize the TeamsClient class
        """
        # configure logger
        self.logger = get_logger(f"{__name__}.{type(self).__name__}")


    def send_message(self, connect_event: Dict[str, str], ddb_event: Dict[str, str]):
        """
        Send a message to a Teams channel
        """
        # extract Amazon Connect message
        content = connect_event.get('Content', None)

        # if content is None, log error and return
        if content is None or len(content) <= 0:
            self.logger.error("Amazon Connect message is empty")
            return None

        # extract teams_auth_header, teams_event from response
        ddb_payload = ddb_event.get('payload', None)
        teams_auth_header = ddb_payload.get('teams_auth_header', None)
        teams_event = ddb_payload.get('teams_event', None)

        # if content contains AGENT_DISCONNECT_MESSAGE, we override content
        # with AGENT_DISCONNECT_MESSAGE_REPLY.  Otherwise, we send the content
        # received from Amazon Connect as is.
        if self.AGENT_DISCONNECT_MESSAGE in content:
            content = self.AGENT_DISCONNECT_MESSAGE_REPLY

        # instantiate ActivityHandler Bot.  The handler will send the
        # reply, i.e. 'content', to user.
        bot = TeamsBot(message=content)

        # instantiate TeamsChatClient
        teams_chat_client = TeamsChatClient(
            auth_header=teams_auth_header,
            bot=bot
        )
        teams_chat_client.process_activity(activity=teams_event)
