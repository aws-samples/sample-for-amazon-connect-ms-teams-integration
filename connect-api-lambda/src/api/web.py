"""web.py - POST /web api implementation."""

from logging import Logger
from chat_clients.common.logging_helper import get_logger
from api.base import BaseApi

class WebApi(BaseApi):
    """
    WebApi contains methods to send chat messages to Amazon Connect
    """
    # class variables
    session_id: str = None
    locale: str = None
    user_name: str = None

    # logger
    logger: Logger = None

    def __init__(self, session_id: str, locale: str, user_name: str):
        # initialize super class
        super().__init__()

        # configure logger
        self.logger = get_logger(f"{__name__}.{type(self).__name__}")

        # set class variables
        self.session_id = session_id
        self.locale = locale
        self.user_name = user_name

    def process(self, message: str) -> str:
        """
        Processes the POST /web request.  Send `message` to Amazon Connect
        Chat API.

        This method will perform following actions:
        - look-up `session_id` in DynamoDB using connect_session_table
          - if record exists, then extract `connection_token`
            - invoke AmazonConnectParticipantServiceClient.send_message with connection_token
          - otherwise
            - call AmazonConnectClient.connect
            - track the response, specially participant_token
            - call AmazonConnectParticipantServiceClient.create_participant_connection
            - track the response, specially, connection_token
            - store all tokens and user info in DynamoDB
            - call AmazonConnectParticipantServiceClient.send_message with connection_token
        - in both cases, return message_id and timestamp to caller that is response from
          AmazonConnectParticipantServiceClient.send_message.  When session_id does not exist
          in DynamoDB, also add "websocket_url" and "connection_expiry" attributes to the response and

        Returns:
            str: response from Amazon Connect

        Raises:
            Exception: if Amazon Connect throws error.
        """
        # look-up session_id in DynamoDB
        response = None
        try:
            response = self.connect_session_table.get_item_by_id(key=self.session_id)
        except:
            # user does not exist so we ignore the exception
            pass

        # if response is not set, then session_id does not exist in DynamoDB
        if not response:
            create_connection_result = self.create_connection(user_name=self.user_name)
            # create payload to store in session store
            payload = {
                "locale": self.locale,
                "user_name": self.user_name,
                "message": message
            }
            self.store_session(key=self.session_id, session_data=create_connection_result, event=payload)
            connection_token = create_connection_result.get("connection_token")
            send_message_result = self.send_message(connection_token=connection_token, message=message)

            # add websocket_url and connection_expiry to response
            result = {
                "session_id": self.session_id,
                "locale": self.locale,
                "message_id": send_message_result.get("message_id"),
                "message_timestamp": send_message_result.get("message_timestamp"),
                "websocket_url": create_connection_result.get("websocket_url"),
                "connection_expiry": create_connection_result.get("connection_expiry")
            }
            return result

        # user exists in DynamoDB
        connection_token = response.get("connection_token")
        send_message_result = self.send_message(connection_token=connection_token, message=message)
        result = {
            "session_id": self.session_id,
            "locale": self.locale,
            "message_id": send_message_result.get("message_id"),
            "message_timestamp": send_message_result.get("message_timestamp")
        }
        return result


