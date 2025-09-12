"""connect_participant.py - Module contains class to interact with Amazon Connect Participant Service APIs"""

import os
from typing import Dict, Any
from logging import Logger
import boto3
from chat_clients.common.logging_helper import get_logger
from chat_clients.common.session_helper import get_boto3_session, get_boto3_client_config
from chat_clients.common.types import ConnectionType, UserChatClientType

class AmazonConnectParticipantServiceClient:
    """
    Class contains client code that establishes connection with Amazon Connect
    Participant Service.  This allows callers to send messages to Amazon
    Connect contact flow.
    """
    # class constants
    DEFAULT_USER_CHAT_CLIENT_TYPE = UserChatClientType.WEB.value

    # connect variables
    client: boto3.client = None
    user_chat_client_type: str = DEFAULT_USER_CHAT_CLIENT_TYPE

    # logger
    logger: Logger = None

    def __init__(self):
        # configure logger
        self.logger = get_logger(f"{__name__}.{type(self).__name__}")

        # initialize env
        self.__init_env()

        # configure boto3 session
        boto3_session = get_boto3_session()
        boto3_client_config = get_boto3_client_config()
        self.client = boto3_session.client(
            'connectparticipant',
            config=boto3_client_config)

    def __init_env(self):
        """
        Read values from environment variables
        """
        # validate USER_CHAT_CLIENT_TYPE contains enumeration defined in UserChatClientType
        user_chat_client_type = os.environ.get("USER_CHAT_CLIENT_TYPE", None)
        if user_chat_client_type and UserChatClientType.is_valid(user_chat_client_type.upper()):
            self.user_chat_client_type = os.environ.get("USER_CHAT_CLIENT_TYPE").upper()

    def __create_websocket_participant_connection(self, participant_token: str) -> Dict[str, Any]:
        """
        Create Amazon Connect Participant Connection using a participant token.
        Participant toke comes from client.connect.connect() call, which invokes
        start_chat_contact API call.

        This method creates a participant connection for contacts that use
        WebSocket protocol, i.e. web applications, SPAs, mobile applications.

        Note that this method will also send CONNECTION_CREDENTIALS type fo the
        create_participant_connection() call without ConnectParticipant=True flag.
        This is done to retrieve `ConnectionToken` from Amazon Connect Participant
        Connection service.  `ConnectionToken` is used in subsequent calls when web
        applications send a chat message.

        Args:
            participant_token (str): Participant token

        Returns:
            Dict[str, Any]: CreateParticipantConnection response
        """
        # create participant connection
        response = self.client.create_participant_connection(
            Type=[
                ConnectionType.WEBSOCKET.value,
                ConnectionType.CONNECTION_CREDENTIALS.value],
            ParticipantToken=participant_token
        )
        # if response is None, raise exception
        if response is None:
            raise Exception("CreateParticipantConnection response is None")

        websocket_details = response.get("Websocket", None)
        if websocket_details is None:
            raise Exception("Websocket details is None")

        url = websocket_details.get("Url", None)
        connection_expiry = websocket_details.get("ConnectionExpiry", None)

        self.logger.debug(
            "CreateParticipantConnection response: WebSocket URL: '%s', Expiry: '%s'",
            url, connection_expiry)

        # also look for connection credentials
        connection_credentials = response.get("ConnectionCredentials", None)
        if connection_credentials is None:
            raise Exception("ConnectionCredentials is None")

        connection_token = connection_credentials.get("ConnectionToken", None)
        token_expiry = connection_credentials.get("Expiry", None)

        result = {
            "websocket_url": url,
            "connection_expiry": connection_expiry,
            "connection_token": connection_token,
            "token_expiry": token_expiry,
        }
        return result

    def __create_connection_credentials_participant_connection(self, participant_token: str) -> Dict[str, Any]:
        """
        Create Amazon Connect Participant Connection using a participant token.
        Participant toke comes from client.connect.connect() call, which invokes
        start_chat_contact API call.

        This method create a participant connection for chat contacts that are not
        using a WebSocket, i.e. third-party chat applications like MS Teams, Slack etc.

        Args:
            participant_token (str): Participant token

        Returns:
            Dict[str, Any]: CreateParticipantConnection response
        """
        # create participant connection
        response = self.client.create_participant_connection(
            Type=[ConnectionType.CONNECTION_CREDENTIALS.value],
            ParticipantToken=participant_token,
            ConnectParticipant=True
        )

        # if response is None, raise exception
        if response is None:
            raise Exception("CreateParticipantConnection response is None")

        connection_credentials = response.get("ConnectionCredentials", None)
        if connection_credentials is None:
            raise Exception("ConnectionCredentials is None")

        connection_token = connection_credentials.get("ConnectionToken", None)
        token_expiry = connection_credentials.get("Expiry", None)

        self.logger.debug(
            "CreateParticipantConnection response: ConnectionToken: '%s', Expiry: '%s'",
            connection_token, token_expiry)
        result = {
            "connection_token": connection_token,
            "token_expiry": token_expiry,
        }
        return result

    def create_participant_connection(self, participant_token: str) -> Dict[str, Any]:
        """
        Create Amazon Connect Participant Connection using a participant token.
        Participant toke comes from client.connect.connect() call, which invokes
        start_chat_contact API call.

        Args:
            participant_token (str): Participant token

        Returns:
            Dict[str, Any]: CreateParticipantConnection response
        """
        # create participant connection

        # if self.user_chat_client_type is WEB then use WEBSOCKET and omit ConnectParticipant,
        if self.user_chat_client_type == UserChatClientType.WEB.value:
            return self.__create_websocket_participant_connection(participant_token)

        # otherwise use CONNECTION_CREDENTIALS
        return self.__create_connection_credentials_participant_connection(participant_token)

    def send_message(self, message: str, connection_token: str) -> Dict[str, Any]:
        """
        Send message to Amazon Connect Participant Service using connection token

        Args:
            message (str): Message to send
            connection_token (str): Amazon Connect connection token from create_participant_connection() call

        Returns:
            Dict[str, Any]: SendMessage response
        """
        # send message
        response = self.client.send_message(
            ContentType="text/plain",
            Content=message,
            ConnectionToken=connection_token)

        self.logger.debug("SendMessage response: %s", response)
        result = {
            "id": response.get("Id", None),
            "time": response.get("AbsoluteTime", None)
        }
        return result

    def send_event(self, event: str, connection_token: str) -> Dict[str, Any]:
        """
        Send event to Amazon Connect Participant Service using connection token

        Args:
            message (str): Message to send
            connection_token (str): Amazon Connect connection token from create_participant_connection() call

        Returns:
            Dict[str, Any]: SendMessage response
        """
        # send event
        response = self.client.send_event(
            ContentType="text/plain",
            Content=event,
            ConnectionToken=connection_token)

        self.logger.debug("SendEvent response: %s", response)
        result = {
            "id": response.get("Id", None),
            "time": response.get("AbsoluteTime", None)
        }
        return result

    def disconnect(self, connection_token: str) -> Dict[str, Any]:
        """
        Disconnect from Amazon Connect Participant Service using connection token

        Args:
            connection_token (str): Amazon Connect connection token from create_participant_connection() call
        """
        # disconnect
        self.client.disconnect_participant(
            ConnectionToken=connection_token)

        self.logger.debug("Disconnect participant response: %s", None)

        # response body is empty when call is successful.  so we return 200 status
        # code indicating operation was successful
        return {"status": 200}
