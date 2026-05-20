"""sns.py - SNS event handler"""

import json
import os
from enum import Enum
from typing import Dict
from logging import Logger
from chat_clients.common.logging_helper import get_logger
from chat_clients.dynamodb.connect_session_table import ConnectSessionTable
from chat_clients.slack.client import SlackClient
# from chat_clients.teams.client import TeamsClient
from teams.teams import TeamsClient

class UserChatClientType(Enum):
    """Supported User Chat Client Type
    """
    WEB = "WEB"
    SLACK = "SLACK"
    TEAMS = "TEAMS"
    # TELEGRAM = "TELEGRAM"
    # more can be added later

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """
        Class method to check if value is a valid type
        """
        return value in [e.value for e in UserChatClientType]

class ConnectParticipantRoleType(Enum):
    """Amazon Connect Participant Service API response Participant Role Type
    """
    AGENT = "AGENT"
    CUSTOMER = "CUSTOMER"
    SYSTEM = "SYSTEM"
    CUSTOM_BOT = "CUSTOM_BOT"
    SUPERVISOR = "SUPERVISOR"

class SNS:
    """
    SNS event handler class.

    SNS
    event can contain multiple records each containing the following
    Amazon Connect Streaming API response payload in the `Message`
    attribute:

    {
        "AbsoluteTime": "2024-02-09T06:34:54.029Z",
        "Content": "The time in queue is less than 5 minutes.",
        "ContentType": "text/plain",
        "Id": "719ba4ad-85c4-469f-88d4-5fff2d524b51",
        "Type": "MESSAGE",
        "ParticipantId": "f4c07fbf-624d-4dd0-aec2-92d247ca685c",
        "DisplayName": "SYSTEM_MESSAGE",
        "ParticipantRole": "SYSTEM",
        "InitialContactId": "0e313287-1aa6-4a89-8108-0dc1a581e017",
        "ContactId": "0e313287-1aa6-4a89-8108-0dc1a581e017"
    }

    `ParticipantRole` can be:

    - AGENT
    - CUSTOMER
    - SYSTEM
    - CUSTOM_BOT
    - SUPERVISOR


    This lambda will process all `ParticipantRole` types except `CUSTOMER`.

    When there is an error during processing, lambda throws an error.

    """
    # class constants
    DEFAULT_USER_CHAT_CLIENT_TYPE = UserChatClientType.SLACK.value

    # class variables
    event: Dict = None
    locale: str = 'en_US'
    connect_session_table: ConnectSessionTable = None
    user_chat_client_type: str = DEFAULT_USER_CHAT_CLIENT_TYPE
    slack_client: SlackClient = None
    teams_client: TeamsClient = None

    logger: Logger = None

    def __init__(self, event: Dict = None) -> None:
        # configure logger
        self.logger = get_logger(f"{__name__}.{type(self).__name__}")

        # initialize env
        self.__init_env()

        # assign class variables
        self.event = event

        # throw error if any of the required fields are missing
        if self.event is None:
            raise Exception("Required fields are missing")

        # instantiate ConnectSessionTable
        self.connect_session_table = ConnectSessionTable()

        # instantiate Slack client
        # self.slack_client = SlackClient()
        self.teams_client = TeamsClient()

    def __init_env(self) -> None:
        """
        Read values from environment variables
        """
        # validate USER_CHAT_CLIENT_TYPE contains enumeration defined in UserChatClientType
        user_chat_client_type = os.environ.get("USER_CHAT_CLIENT_TYPE", None)
        if user_chat_client_type and UserChatClientType.is_valid(user_chat_client_type.upper()):
            self.user_chat_client_type = os.environ.get("USER_CHAT_CLIENT_TYPE", "").upper()

    def process(self) -> str:
        """
        process sns event

        outer SNS event.
        - each record contains 'EventSource' attribute with value "aws:sns",
        - each record contains 'Sns' attribute which is a dictionary containing,
          - 'Type' with a value of 'Notification'
          - 'MessageId' with a unique identifier for the message
          - 'TopicArn' with the ARN of the topic the message was published to
          - 'Subject' with the subject of the message
          - 'Message' attribute which is a JSON string containing the SNS message
          - 'Timestamp' with the time the message was published
          - 'SignatureVersion' with the signature version of the message
          - 'Signature' with the signature of the message
          - 'SigningCertURL' with the URL of the signing certificate
          - 'UnsubscribeURL' with the URL to unsubscribe from the topic
          - 'MessageAttributes' with the message attributes of the message

        This method deserialize the 'Message' attribute and calls Slack Events
        API to send message back to the caller.

        Upon successful completion, method returns a success message.  It
        throws an error if failure occurs at any time during processing.

        Returns:
            str: successful response
        """

        try:
            for i, record in enumerate(self.event.get('Records', [])):
                parsed_event = json.loads(record.get('Sns', {}).get('Message', '{}'))
                self.logger.debug("SNS Record %d, Parsed event: %s", i+1, json.dumps(parsed_event, indent=2))

                # extract the event from the parsed SNS message
                # if parsed_event:
                content = parsed_event.get('Content', None)
                message_id = parsed_event.get('Id', None)
                message_type = parsed_event.get('Type', None)
                contact_id = parsed_event.get('ContactId', None)
                initial_contact_id = parsed_event.get('InitialContactId', None)
                participant_role = parsed_event.get('ParticipantRole', None)
                content_type = parsed_event.get('ContentType', None)

                # validate if any values are None, then continue
                if message_id is None or message_type is None or contact_id is None or initial_contact_id is None or participant_role is None:
                    self.logger.debug(
                        "Skipping SNS message with missing values. 'Id', 'Type', 'ContactId', 'InitialContactId', 'ParticipantRole' are required.  received event: %s",
                        json.dumps(parsed_event, indent=2))
                    continue

                if participant_role == ConnectParticipantRoleType.CUSTOMER.value:
                    self.logger.debug("Skipping SNS message with participant role: %s", participant_role)
                    continue

                # determine user's chat client type to use
                if self.user_chat_client_type == UserChatClientType.SLACK.value:
                    # look up contact_id in DDB
                    response = self.connect_session_table.get_item_by_contact_id(key=contact_id)
                    # extract id as user_id from response
                    user_id = response.get('id', None)
                    # Use Slack client to send message, i.e. 'content' from SNS to 'user_id' retrieved from DDB
                    self.slack_client.send_message(message=content, target=user_id)
                elif self.user_chat_client_type == UserChatClientType.TEAMS.value:
                    # compare contact_id and initial_contact_id, if they are same, use contact_id to
                    # retrieve teams event from DDB. otherwise, use initial_contact_id.
                    chat_session_table_key = contact_id if contact_id == initial_contact_id else initial_contact_id

                    # look up contact_id in DDB
                    response = self.connect_session_table.get_item_by_contact_id(key=chat_session_table_key)

                    # Detect agent joining via the participant-joined EVENT (fired before the
                    # agent's first message) and set the flag immediately. This gives the DDB
                    # write the maximum possible lead time before the user can respond to the
                    # agent's greeting, avoiding the race condition where the user replies
                    # before agent_joined=True has propagated.
                    is_agent_joined_event = (
                        participant_role == ConnectParticipantRoleType.AGENT.value
                        and message_type == "EVENT"
                        and content_type == "application/vnd.amazonaws.connect.event.participant.joined"
                    )
                    # Also set on the agent's first MESSAGE as a fallback, in case the
                    # joined event was missed or arrived out of order.
                    is_agent_message = (
                        participant_role == ConnectParticipantRoleType.AGENT.value
                        and message_type == "MESSAGE"
                    )
                    if is_agent_joined_event or is_agent_message:
                        user_id = response.get("id")
                        if user_id and not response.get("agent_joined", False):
                            try:
                                self.connect_session_table.set_agent_joined(key=user_id)
                                self.logger.debug(
                                    "Agent joined — set agent_joined=True for user_id='%s' "
                                    "(trigger: %s)",
                                    user_id,
                                    "participant.joined event" if is_agent_joined_event else "first agent message"
                                )
                            except Exception as e:
                                self.logger.error(
                                    "Failed to set agent_joined for user_id='%s': %s", user_id, e)

                    # Only forward MESSAGE type events to Teams — skip participant
                    # joined/left events and other non-message events.
                    if message_type != "MESSAGE" or content is None:
                        self.logger.debug(
                            "Skipping non-message SNS event: type='%s', content_type='%s'",
                            message_type, content_type)
                        continue

                    # send teams message
                    self.teams_client.send_message(
                        connect_event=parsed_event,
                        ddb_event=response
                    )

                else:
                    # unsupported chat client type
                    self.logger.error("Unsupported chat client type: %s", self.user_chat_client_type)

        except Exception as e:
            error_message = "Failed to process SNS message: " + str(e)
            self.logger.error(error_message)
            raise Exception(error_message) from e

        return "successfully processed SNS event"
