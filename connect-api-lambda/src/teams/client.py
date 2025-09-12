"""client.py - Module class a wrapper class that calls Chat SDK TeamsClient"""
from logging import Logger
from typing import Any, Dict
from botbuilder.core import ActivityHandler
from chat_clients.common.logging_helper import get_logger
from chat_clients.teams.client import TeamsClient as TeamsClientBase

class TeamsClient(TeamsClientBase):
    """
    TeamsClient extends Chat Client SDK TeamsClient
    """
    # logger
    logger: Logger = None

    """TeamsClient extends Chat Client SDK TeamsClient"""
    def __init__(self, auth_header: str, bot: ActivityHandler = None):
        super().__init__(auth_header=auth_header, bot=bot)

        # configure logger
        self.logger = get_logger(f"{__name__}.{type(self).__name__}")

    def process_activity(self, activity: Dict[str, Any]) -> Dict:
        """
        Call the super class process activity.  This is a place
        holder method where you can do additional processing of the
        teams event (activity) if necessary.

        Args:
            activity (Dict[str, Any]): teams activity payload

        Returns:
            Dict: Response from teams client
        """
        self.logger.debug("Invoking ")
        return super().process_activity(activity)
