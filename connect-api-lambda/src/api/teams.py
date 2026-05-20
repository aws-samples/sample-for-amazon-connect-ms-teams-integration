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

        # initialize instance variables (not class-level to avoid cross-invocation bleed)
        self.auth_header = auth_header
        self.payload = payload
        self.is_connect_chat_disconnected = False
        self.is_connect_chat_enabled = False
        self.user_id = None
        self.user_name = None
        self.user_query = None
        # Cache the DDB session for the lifetime of this request to avoid
        # multiple reads of the same item (is_new_chat, is_agent_active, process_chat
        # all need it). Set to sentinel so we can distinguish "not yet fetched"
        # from "fetched and not found" (None).
        self._session_cache: Dict[str, Any] = {}
        self._session_fetched: bool = False

        # initialize TeamsBot and TeamsClient
        bot = TeamsBot(
            is_new_chat_callback=self.__is_new_chat_session,
            is_agent_active_callback=self.__is_agent_active,
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

    def __get_cached_session(self, user_id: str) -> Dict[str, Any]:
        """
        Return the DDB session for user_id, fetching it at most once per
        Lambda invocation. All three callers (is_new_chat, is_agent_active,
        process_chat) share the same result, reducing DDB reads from 3 to 1.
        """
        if not self._session_fetched:
            self._session_cache = self.get_session(key=user_id) or {}
            self._session_fetched = True
        return self._session_cache

    def __invalidate_session_cache(self) -> None:
        """Force a fresh DDB read on the next __get_cached_session call."""
        self._session_fetched = False
        self._session_cache = {}

    def __is_agent_active(self, user_id: str) -> bool:
        """
        Returns True if a live agent has joined this user's chat session.
        Used by TeamsBot to suppress the typing acknowledgement during
        live-agent conversations.
        """
        session = self.__get_cached_session(user_id)
        return bool(session.get("agent_joined", False))

    def __is_new_chat_session(self, user_id: str) -> bool:
        """
        Method checks for user session exists in DDB.  If session
        entry with `user_id` as key exists in DDB table, then user
        has previously started a chat session.  Return False in this
        case.  Otherwise, return True.

        Args:
            user_id (str): Teams user id

        Returns:
            bool: True if this is a new session (no DDB record found).
        """
        session = self.__get_cached_session(user_id)
        return len(session) == 0

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

        # check if user is set — fall back to user_id if name was not provided by Teams
        # (from_property.name is absent for guest/federated accounts)
        if not self.user_name:
            self.logger.warning(
                "user_name is not set for user_id '%s', falling back to user_id as display name",
                self.user_id
            )
            self.user_name = self.user_id

        # check if text is set
        if not self.user_query:
            error_message = {
                "error": "user_query is not set."
            }
            self.logger.error("Error: %s", json.dumps(error_message, indent=2))
            return error_message

        # look-up user chat session in DynamoDB (uses cache — already fetched by callbacks)
        cached = self.__get_cached_session(self.user_id)
        response = cached if cached else None

        try:
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
            self.__invalidate_session_cache()

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
        # It's a brand new chat session, or the previous token expired/contact ended.
        # Delete any stale DDB record before creating a fresh connection so the next
        # invocation doesn't attempt to reuse an invalid token.
        if not response or request_failed:
            if request_failed:
                self.logger.warning(
                    "Previous connection token invalid for user '%s' (AccessDeniedException) — "
                    "contact likely ended. Deleting stale session and starting a new Connect contact.",
                    self.user_id
                )
                self.delete_session(key=self.user_id)

            create_connection_result = self.create_connection(user_name=self.user_name)
            self.store_session(key=self.user_id, session_data=create_connection_result, event=event)
            self.__invalidate_session_cache()
            connection_token = create_connection_result.get("connection_token")

            if request_failed:
                # Mid-conversation reconnect: the contact ended unexpectedly (idle timeout,
                # flow completion, etc.) while the user was still chatting. Send their
                # message to the new contact so it reaches Lex and the conversation continues.
                send_message_result = self.send_message(connection_token=connection_token, message=self.user_query)
                return {
                    "message_id": send_message_result.get("message_id"),
                    "message_timestamp": send_message_result.get("message_timestamp"),
                }

            # Brand-new session (no prior DDB record): do NOT send the triggering message.
            #
            # The contact flow's Lex block sends an initial prompt ("How can I help you
            # today?") and then waits for the user's first input. If we immediately send
            # the message that triggered session creation (e.g. "Hello"), Lex receives it
            # as the answer to its own prompt — "Hello" matches no intent, hits
            # NoMatchingCondition, and the flow ends or loops before the user's real
            # question is ever sent.
            #
            # Instead, let the contact flow prompt the user via SNS → connect-stream-lambda
            # → Teams. The user's NEXT message will be the first real input to Lex, sent
            # via the existing-session path using the stored connection_token.
            self.logger.debug(
                "New Connect session established for user '%s'. "
                "Waiting for contact flow prompt before forwarding user messages.",
                self.user_id
            )
            return {}
