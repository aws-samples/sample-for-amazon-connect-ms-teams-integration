
import json
from typing import Any, Dict, Optional
from logging import Logger
from chat_clients.common.logging_helper import get_logger
from chat_clients.dynamodb.connect_session_table import ConnectSessionTable
from chat_clients.connect.client import AmazonConnectClient
from chat_clients.connect.participant_service_client import AmazonConnectParticipantServiceClient

class BaseApi:
    """
    Base API class with common routines used by all
    API subclasses.
    """
    connect_session_table: ConnectSessionTable = None
    connect_client: AmazonConnectClient = None
    participant_service_client: AmazonConnectParticipantServiceClient = None

    # logger
    logger: Logger = None

    def __init__(self):
        # configure logger
        self.logger = get_logger(f"{__name__}.{type(self).__name__}")

        # instantiate ConnectSessionTable
        self.connect_session_table = ConnectSessionTable()

        # instantiate connect clients
        self.connect_client = AmazonConnectClient()
        self.participant_service_client = AmazonConnectParticipantServiceClient()

    def create_connection(self, user_name: str) -> Dict[str, str]:
        """
        Create connection with Amazon Connect.

        Args:
            user_name (str): Slack user name.

        Returns:
            Dict[str, str]: response indicating that the connection was created.
        """
        if not user_name or len(user_name) == 0:
            error_message = {
                "error": "User name is not set."
            }
            self.logger.error("Error: %s", json.dumps(error_message, indent=2))
            return error_message

        # call AmazonConnectClient.connect)
        result = self.connect_client.connect(user_name=user_name)
        # extract contact_id, participant_id, participant_token
        contact_id = result.get("contact_id")
        participant_id = result.get("participant_id")
        participant_token = result.get("participant_token")
        streaming_id = result.get("streaming_id", None)

        # call AmazonConnectParticipantServiceClient.create_participant_connection
        participant_result = self.participant_service_client.create_participant_connection(
            participant_token=participant_token)
        # track the response, specially, connection_token
        connection_token = participant_result.get("connection_token")
        token_expiry = participant_result.get("token_expiry")
        websocket_url = participant_result.get("websocket_url")
        connection_expiry = participant_result.get("connection_expiry")

        response = {
            "user_name": user_name,
            "contact_id": contact_id,
            "participant_id": participant_id,
            "participant_token": participant_token,
            "streaming_id": streaming_id,
            "connection_token": connection_token,
            "token_expiry": token_expiry,
            "websocket_url": websocket_url,
            "connection_expiry": connection_expiry
        }
        # remove attribute from response with None value
        response = {k: v for k, v in response.items() if v is not None}

        self.logger.debug("Response: %s", json.dumps(response, indent=2))
        return response

    def stop_connection(self, contact_id: str, streaming_id: str, connection_token: str) -> Dict[str, str]:
        """
        Stop connection with Amazon Connect.

        Args:
            contact_id (str): Amazon Connect contact id.
            streaming_id (str): Amazon Connect streaming id.
            connection_token (str): Amazon Connect connection token.

        Returns:
            Dict[str, str]: response indicating that the connection was stopped.
        """
        # call AmazonConnectClient.disconnect()
        result = self.connect_client.disconnect(contact_id=contact_id, streaming_id=streaming_id)

        # call AmazonConnectParticipantServiceClient.disconnect()
        self.participant_service_client.disconnect(connection_token=connection_token)

        return result

    def store_session(self, key: str, session_data: Dict[str, str], event: Dict[str, Any]) -> None:
        """
        Store Amazon Connect chat session data in DynamoDB.

        Args:
            session_data (Dict[str, str]): session data is the response from __create_connection() call.
            event (Dict[str, Any]): Slack event to store in DynamoDB.
        """

        table_hash_key = key
        contact_id = session_data.get("contact_id")
        participant_id = session_data.get("participant_id")
        participant_token = session_data.get("participant_token")
        connection_token = session_data.get("connection_token")
        streaming_id = session_data.get("streaming_id")

        # store all tokens and user info in DynamoDB
        try:
            self.connect_session_table.add_item(
                key=table_hash_key,
                contact_id=contact_id,
                participant_id=participant_id,
                participant_token=participant_token,
                streaming_id=streaming_id,
                connection_token=connection_token,
                payload=event)
        except Exception as e:
            self.logger.error("Error: %s", e)

    def update_session(self, key: str, session_data: Optional[Dict[str, str]] = None, event: Optional[Dict[str, Any]] = None) -> None:
        """
        Update Amazon Connect chat session data in DynamoDB.

        Args:
            session_data (Dict[str, str]): session data is the response from __create_connection() call.
            event (Dict[str, Any]): Slack event to store in DynamoDB.
        """
        table_hash_key = key
        contact_id = session_data.get("contact_id") if session_data else None
        participant_id = session_data.get("participant_id") if session_data else None
        participant_token = session_data.get("participant_token") if session_data else None
        connection_token = session_data.get("connection_token") if session_data else None
        streaming_id = session_data.get("streaming_id") if session_data else None
        payload = event if event else None

        # update all tokens and user info in DynamoDB
        try:
            self.connect_session_table.update_item(
                key=table_hash_key,
                contact_id=contact_id,
                participant_id=participant_id,
                participant_token=participant_token,
                streaming_id=streaming_id,
                connection_token=connection_token,
                payload=payload)
        except Exception as e:
            self.logger.error("Error: %s", e)

    def delete_session(self, key: str) -> None:
        """
        Delete Amazon Connect chat session data from DynamoDB.

        Args:
            key (str): key is the user name.
        """
        try:
            self.connect_session_table.delete_item(key=key)
        except Exception as e:
            self.logger.error("Error: %s", e)


    def get_session(self, key: str) -> Dict[str, str]:
        """
        Get Amazon Connect chat session data from DynamoDB.

        Args:
            key (str): key is the user name.

        Returns:
            Dict[str, str]: session data is the response from __create_connection() call.
        """
        try:
            response = self.connect_session_table.get_item_by_id(key=key)
        except Exception as e:
            self.logger.warning("key %s not found.  error: %s", key, e)
            response = None

        return response

    def send_message(self, connection_token: str, message: str) -> Dict[str, str]:
        """
        Send message to Amazon Connect.

        Args:
            connection_token (str): connection token.
            message (str): message to send.

        Returns:
            Dict[str, str]: response indicating that the message was sent.
        """
        # call AmazonConnectParticipantServiceClient.send_message
        participant_service_client = AmazonConnectParticipantServiceClient()
        result = participant_service_client.send_message(message=message, connection_token=connection_token)

        # extract message_id, timestamp
        message_id = result.get("id")
        message_timestamp = result.get("time")

        response = {
            "message_id": message_id,
            "message_timestamp": message_timestamp,
        }
        self.logger.debug("Response: %s", json.dumps(response, indent=2))
        return response
