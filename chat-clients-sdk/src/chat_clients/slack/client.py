"""slack.py - Slack client class that sends message to a user or channel."""

import json
import os
from logging import Logger
import requests
from chat_clients.common.logging_helper import get_logger

class SlackClient:
    """
    This class uses the Slack `chat.postMessage` API to send a message to a user
    or channel.
    """
    # class constants
    DEFAULT_SLACK_CHAT_POST_MESSAGE_API_URL = "https://slack.com/api/chat.postMessage"
    DEFAULT_SLACK_API_TIMEOUT: int = 60 # seconds

    # class variables
    slack_chat_post_message_api_url: str = DEFAULT_SLACK_CHAT_POST_MESSAGE_API_URL
    slack_oauth_token: str = None
    logger: Logger = None

    def __init__(self) -> None:
        # configure logger
        self.logger = get_logger(f"{__name__}.{type(self).__name__}")

        # initialize env
        self.__init_env()

    def __init_env(self) -> None:
        """
        Read values from environment variables
        """

        # SLACK_CHAT_POST_MESSAGE_API_URL
        self.slack_chat_post_message_api_url = os.environ.get(
            "SLACK_CHAT_POST_MESSAGE_API_URL",
            self.DEFAULT_SLACK_CHAT_POST_MESSAGE_API_URL)

        # SLACK_APP_WORKSPACE_TOKEN
        self.slack_oauth_token = os.environ.get("SLACK_APP_WORKSPACE_TOKEN", None)
        if not self.slack_oauth_token or len(self.slack_oauth_token) == 0:
            error_message = "SLACK_APP_WORKSPACE_TOKEN environment variable must be set"
            self.logger.error(error_message)
            raise Exception(error_message)

    def send_message(self, message: str, target: str) -> None:
        """
        Send message to a user or channel.  `target` represents either a channel
        or user.  Inside the Slack chat.postMessage API we set the `channel` attribute
        to target a user or channel.

        Args:
            message (str): message to send to user or channel in Slack
            target (str): target Slack user or channel
        """
        if not message or len(message) == 0:
            self.logger.warning("message is empty")
            return

        if not target or len(target) == 0:
            self.logger.warning("target is empty")
            return

        # set request header with Authorization Bearer token
        # and content type to application/json
        request_header = {
            "Authorization": f"Bearer {self.slack_oauth_token}",
            "Content-type": "application/json"
        }
        # set request body
        request_body = {
            "channel": target,
            "text": message
        }
        # send request
        response = requests.post(
            self.slack_chat_post_message_api_url,
            headers=request_header,
            json=request_body,
            timeout=self.DEFAULT_SLACK_API_TIMEOUT
        ).json()

        # check for error
        if 'error' in response:
            error_message = "Failed to send message to Slack: " + str(response['error'])
            self.logger.error("%s. error details: %s", error_message, json.dumps(response, indent=2))
            raise Exception(error_message)

        # extract ts, channel, team and bot profile from response
        ts = response.get('ts', None)
        channel = response.get('channel', None)
        team = response.get('team', None)
        response_message = response.get('message', None)
        bot_profile = response_message.get('bot_profile', None)
        bot_id = None
        bot_name = None
        app_id = None
        if bot_profile is not None:
            bot_id = bot_profile.get('id', None)
            bot_name = bot_profile.get('name', None)
            app_id = bot_profile.get('app_id', None)

        # create log payload
        log_payload = {
            "target": target,
            "message": message,
            "ts": ts,
            "channel": channel,
            "team": team,
            "bot_id": bot_id,
            "bot_name": bot_name,
            "app_id": app_id
        }

        # remove None values from log payload
        log_payload = {k: v for k, v in log_payload.items() if v is not None}

        self.logger.debug("response: %s", json.dumps(log_payload, indent=2))
