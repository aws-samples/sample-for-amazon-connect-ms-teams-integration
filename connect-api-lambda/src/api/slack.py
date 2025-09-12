"""slack.py - POST /slack api implementation. Payload to API is Slack Event API message"""

import json
from typing import Dict
from logging import Logger
from chat_clients.common.logging_helper import get_logger
from api.base import BaseApi

class SlackApi(BaseApi):
    """
    This class handles Slack Event API messages.
    """
    # class variables
    payload: str = None

    # logger
    logger: Logger = None

    def __init__(self, payload: str):
        # initialize super class
        super().__init__()

        # configure logger
        self.logger = get_logger(f"{__name__}.{type(self).__name__}")

        # set class variables
        self.payload = payload

    def __process_im_event(self) -> Dict[str, str]:
        """
        Process Slack `event_callback` type `event`.  The `event` contains
        `channel_type` attribute that indicates what type of message to
        process.  This method only handles `im` messages.

        This method will perform following actions:
        - extract following attributes from `event`
          - `user`
          - `text`
          - `ts`
          - `team`
          - `channel`
        - look-up `user` in DynamoDB using connect_session_table
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
          AmazonConnectParticipantServiceClient.send_message

        Args:
            event (Dict[str, str]): Slack event.

        Returns:
            Dict[str, str]: response indicating that the message was processed

        """
        # extract event from payload
        event = self.payload.get('event', {})
        if not event:
            error_message = {
                "error": "Event is not set."
            }
            self.logger.error("Error: %s", json.dumps(error_message, indent=2))
            return error_message

        # extract attributes from event
        user = event.get('user', None)
        text = event.get('text', None)

        # check if user is set
        if not user:
            error_message = {
                "error": "User is not set."
            }
            self.logger.error("Error: %s", json.dumps(error_message, indent=2))
            return error_message

        # check if text is set
        if not text:
            error_message = {
                "error": "Text is not set."
            }
            self.logger.error("Error: %s", json.dumps(error_message, indent=2))
            return error_message

        # look-up user in DynamoDB
        response = None
        try:
            response = self.connect_session_table.get_item_by_id(key=user)
        except:
            # user does not exist so we ignore the exception
            pass

        # if response is not set, then user does not exist in DynamoDB
        if not response:
            create_connection_result = self.create_connection(user_name=user)
            self.store_session(key=user, session_data=create_connection_result, event=event)
            connection_token = create_connection_result.get("connection_token")
            send_message_result = self.send_message(connection_token=connection_token, message=text)
            result = {
                "message_id": send_message_result.get("message_id"),
                "message_timestamp": send_message_result.get("message_timestamp"),
            }
            return result

        # user exists in DynamoDB
        connection_token = response.get("connection_token")
        send_message_result = self.send_message(connection_token=connection_token, message=text)
        result = {
            "message_id": send_message_result.get("message_id"),
            "message_timestamp": send_message_result.get("message_timestamp"),
        }
        return result

    def __process_url_verification(self) -> Dict[str, str]:
        """
        Process Slack 'url_verification' event type.

        Returns:
            Dict[str, str]: response indicating challenge to Slack.
        """
        challenge = self.payload.get('challenge', None)
        if not challenge:
            error_message = {
                "error": "Challenge is not set."
            }
            self.logger.error("Error: %s", json.dumps(error_message, indent=2))
            return error_message

        response = {"challenge": challenge}
        self.logger.debug("Response: %s", json.dumps(response, indent=2))
        return response

    def __process_error_message(self, error_message: str) -> Dict[str, str]:
        """
        Process Slack error message.

        Args:
            error_message (str): error message.

        Returns:
            Dict[str, str]: response indicating that the error message was processed.
        """
        response = {"error": error_message}
        self.logger.debug("Response: %s", json.dumps(response, indent=2))
        return response

    def process(self) -> Dict[str, str]:
        """
        Slack payload can consist of following event `type`:

        - url_verification
        - event_callback

        url_verification event type payload is as follows:
        {
            "token": "Jhj5dZrVaK7ZwHHjRyZWjbDl",
            "challenge": "abcd12342rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7tYXAYM8P",
            "type": "url_verification"
        }

        event_callback payload has following format:
        {
            "token": "ABCDEF",
            "team_id": "ABCDEF",
            "context_team_id": "ABCDEF",
            "context_enterprise_id": null,
            "api_app_id": "ABCDEF",
            "event": {
                "client_msg_id": "51570646-ABCDEF",
                "type": "message",
                "text": "Hello",
                "user": "ABCDEF",
                "ts": "1707119042.279709",
                "blocks": [
                    {
                        "type": "rich_text",
                        "block_id": "ABCDEF",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type": "text",
                                        "text": "Hello"
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "team": "ABCDEF",
                "channel": "ABCDEF",
                "event_ts": "1707119042.279709",
                "channel_type": "im"
            },
            "type": "event_callback",
            "event_id": "ABCDEF",
            "event_time": 1707119042,
            "authorizations": [
                {
                    "enterprise_id": null,
                    "team_id": "ABCDEF",
                    "user_id": "ABCDEF",
                    "is_bot": true,
                    "is_enterprise_install": false
                }
            ],
            "is_ext_shared_channel": false,
            "event_context": "4-ABCDEF"
        }

        This method calls __process_url_verification() if type is url_verification.
        Otherwise, it calls __process_im_event() if type is event_callback.

        Returns:
            Dict[str, str]: response indicating challenge to Slack.
            Dict[str, str]: response indicating that the message was processed.
        """

        try:
            # get event type from Slack payload
            event_type = self.payload.get('type', None)

            if not event_type:
                error_message = "Payload type is not set."
                return self.__process_error_message(error_message)

            # process Slack url_verification event type
            if event_type == "url_verification":
                return self.__process_url_verification()

            # process Slack event_callback event type
            elif event_type == "event_callback":

                # if channel_type == im, then it's a direct message,
                # if channel_type == channel, then it's a channel message
                # if channel_type == group, then it's a group message
                # otherwise not supported
                channel_type = self.payload.get('event', {}).get('channel_type', None)
                if not channel_type:
                    error_message = "Channel type is not set."
                    return self.__process_error_message(error_message)
                elif channel_type == "im":
                    return self.__process_im_event()
                else:
                    error_message = f"Unsupported channel type: {channel_type}"
                    return self.__process_error_message(error_message)

            # Other event types are not supported
            error_message = f"Unsupported payload type: {event_type}"
            return error_message

        except Exception as e:
            error_message = f"Error: {e}"
            self.logger.error(error_message)
            return self.__process_error_message(error_message)
