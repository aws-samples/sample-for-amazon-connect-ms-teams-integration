"""teams.py - POST /teams api implementation. Payload to API is Azure Bot Service message"""

import json
from typing import Any, Dict
from logging import Logger
from chat_clients.common.logging_helper import get_logger
from api.base import BaseApi
from teams.bot import TeamsBot
from teams.client import TeamsClient

class TeamsApi(BaseApi):
    """
    This class handles Azure Bot service messages.
    """
    # class variables
    auth_header: str = None
    payload: Dict[str, Any] = None
    teams_client: TeamsClient = None
    is_connect_chat_disconnected: bool = False
    is_connect_chat_enabled: bool = False
    user_id: str = None
    user_name: str = None
    user_query: str = None

    # logger
    logger: Logger = None

    def __init__(self, auth_header: str, payload: Dict[str, Any]):
        # initialize super class
        super().__init__()

        # configure logger
        self.logger = get_logger(f"{__name__}.{type(self).__name__}")

        # initialize class variables
        self.auth_header = auth_header
        self.payload = payload

        # initialize TeamsBot and TeamsClient
        bot = TeamsBot(
            is_new_chat_callback=self.__is_new_chat_session,
            set_data_callback=self.__set_chat_data
        )
        self.teams_client = TeamsClient(auth_header=self.auth_header, bot=bot)

    def process(self) -> Dict[str, str]:
        """
        Process Teams event.
        """
        response = self.teams_client.process_activity(activity=self.payload)

        if self.is_connect_chat_enabled:
            connect_response = self.__process_amazon_connect_chat()
            # add dictionary values from connect_response to response
            response.update(connect_response)

        # response is a dictionary and it can contain following attribute
        # - status: MS Teams bot framework status code
        # - message_id: Amazon Connect message id.  This indicate message was accepted by Amazon Connect
        # - message_timestamp: Amazon Connect message acceptance timestamp.
        return response

    def __set_chat_data(self,
        user_query: str,
        user_id: str,
        user_name: str,
        is_connect_chat_enabled: bool,
        is_connect_chat_disconnected: bool = False
    ) -> None:
        """
        Set following class variables that are needed to initiate Amazon Connect chat.

        - user_id
        - user_name
        - user_query
        - is_connect_chat_enabled

        Following class variable indicates whether we should disconnect Amazon Connect chat
        and delete chat session table entries.

        - is_connect_chat_disconnected

        """
        self.user_id = user_id
        self.user_name = user_name
        self.user_query = user_query
        self.is_connect_chat_disconnected = is_connect_chat_disconnected
        self.is_connect_chat_enabled = is_connect_chat_enabled
        if self.is_connect_chat_enabled:
            self.logger.debug("Amazon Connect chat enabled")

    def __is_new_chat_session(self, user_id: str) -> bool:
        """
        Method checks for user session exists in DDB.  If session
        entry with `user_id` as key exists in DDB table, then user
        has previously started a chat session.  Return False in this
        case.  Otherwise, return True.

        Args:
            user_id (str): Teams user id

        Returns:
            bool: Boolean value indicating if user has started a chat session.  If True, then user has not started a chat session.  If False, then user has started a chat session.
        """
        # look-up user chat session in DynamoDB
        response = self.get_session(key=user_id)

        # if response is not set, then user does not exist in DynamoDB
        if not response:
            return True

        # user exists in DynamoDB
        return False

    def __process_amazon_connect_chat(self) -> Dict[str, str]:
        """_summary_

        Returns:
            Dict[str, str]: _description_
        """
        # create event to store in DDB
        event = {
            "teams_user_name":  self.user_name,
            "teams_auth_header":  self.auth_header,
            "teams_event": self.payload,
        }

        # check if user is set
        if not self.user_name:
            error_message = {
                "error": "User is not set."
            }
            self.logger.error("Error: %s", json.dumps(error_message, indent=2))
            return error_message

        # check if text is set
        if not self.user_query:
            error_message = {
                "error": "user_query is not set."
            }
            self.logger.error("Error: %s", json.dumps(error_message, indent=2))
            return error_message

        # look-up user chat session in DynamoDB
        response = None
        try:
            response = self.get_session(key=self.user_id)

            # if response is not None, a chat session exits in DDB.  We must
            # update the session entry in DDB with new teams event.
            if response:
                self.update_session(key=self.user_id, event=event)
        except Exception as e:
            # user does not exist so we ignore the exception
            self.logger.error("Error looking up session: %s", str(e))

        # if user requested to disconnect chat session, then perform clean-up
        if self.is_connect_chat_disconnected:
            if not response:
                error_message = "No existing chat session.  Skipping disconnect."
                self.logger.debug(error_message)
                error_response = {
                    "error_message":  error_message
                }
                return error_response

            # delete user chat session in DDB
            self.delete_session(key=self.user_id)

            # get contact_id, streaming_id, and connection_token from response
            contact_id = response.get("contact_id")
            streaming_id = response.get("streaming_id")
            connection_token = response.get("connection_token")

            # validate contact_id, streaming_id, and connection_token
            if not contact_id or not streaming_id or not connection_token:
                error_message = "Unable to retrieve contact_id, streaming_id, or connection_token."
                self.logger.error(error_message)
                error_response = {
                    "error_message":  error_message
                }
                return error_response

            # disconnect Amazon Connect chat
            result = self.stop_connection(contact_id=contact_id, streaming_id=streaming_id, connection_token=connection_token)
            # response will contain {"status": 200} if we disconnected successfully
            return result

        # If user exists in DynamoDB, reuse Amazon Connect connection token and send a message to Amazon Connect contact flow
        connection_token = response.get("connection_token") if response else None

        request_failed = False
        # Try sending a message with the old token, if this fails, we try a new token
        # Try catch because the token may have expired
        if connection_token:
            try:
                send_message_result = self.send_message(connection_token=connection_token, message=self.user_query)
                result = {
                    "message_id": send_message_result.get("message_id"),
                    "message_timestamp": send_message_result.get("message_timestamp"),
                }
                return result
            except Exception as e:
                request_failed = True
                self.logger.error("Issue during send_message: %s", e)

        # if response is not set, then user does not exist in DynamoDB.
        #  It's a brand new chat session.
        if not response or request_failed:
            create_connection_result = self.create_connection(user_name=self.user_name)
            self.store_session(key=self.user_id, session_data=create_connection_result, event=event)
            connection_token = create_connection_result.get("connection_token")
            send_message_result = self.send_message(connection_token=connection_token, message=self.user_query)
            result = {
                "message_id": send_message_result.get("message_id"),
                "message_timestamp": send_message_result.get("message_timestamp"),
            }
            return result
