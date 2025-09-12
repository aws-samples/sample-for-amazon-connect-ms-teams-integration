"""teams_bot.py - module contains Teams bot that handles user questions"""

from typing import List, Callable
from logging import Logger
from chat_clients.common.logging_helper import get_logger
from botbuilder.core import ActivityHandler, TurnContext, CardFactory
from botbuilder.schema import ChannelAccount, Attachment, Activity, ActivityTypes

FAQ_LIST = [
    "How do I reset my Windows password?",
    "How do I reset my Mac password?",
    "How do I setup WIFI in Windows 10?",
    "Chat with Agent"
]
ACKNOWLEDGEMENT_MESSAGE = "Please give me a few moments to process your request."
ADAPTIVE_CARD_KEYWORDS = ["hi", "hello", "menu"]

DISCONNECT_MESSAGE = "Thank you for using Amazon Connect chat. Have a nice day!"
DISCONNECT_KEYWORDS = ["bye", "exit", "quit", "disconnect", "close"]

class TeamsBot(ActivityHandler):
    """
    This bot handles Azure Bot Service API request that originate from MS Teams.
    It responds to the user's input.  Input can contain one of the following
    elements:

    - a plain text message, i.e. a greeting or command "hello", "hi", "menu"
    - a question that can come in plain text field or as part of value object

    When the question contains ADAPTIVE_CARD_KEYWORDS, the bot will send back an
    an Adaptive Card. Adaptive Card contains questions from the FAQ_LIST.

    When the question is not in the FAQ_LIST, the bot will send back a textual
    response, i.e. ACKNOWLEDGEMENT_MESSAGE.
    """
    # class variables
    set_data_callback: Callable = None
    is_new_chat_callback: Callable = None

    # logger
    logger: Logger = None

    def __init__(self, is_new_chat_callback: Callable, set_data_callback: Callable):
        super().__init__()

        # configure logger
        self.logger = get_logger(f"{__name__}.{type(self).__name__}")

        # initialize class variables
        self.is_new_chat_callback = is_new_chat_callback
        self.set_data_callback = set_data_callback

    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    f"Hello and welcome {member.name}!"
                )

    async def on_message_activity(self, turn_context: TurnContext):
        # extract user question from either turn_context.activity.text or turn_context.activity.value.button
        # if turn_context.activity.text is not empty, use turn_context.activity.text
        # otherwise turn_context.activity.value.button
        question = turn_context.activity.text if turn_context.activity.text else turn_context.activity.value.get("button", None)

        # if question is not set, return
        if not question:
            self.logger.debug("Question is empty.  Turn context activity: %s", str(turn_context.activity))
            # disable amazon connect chat invocation
            self.set_data_callback(
                    user_query=question,
                    user_id=turn_context.activity.from_property.id,
                    user_name=turn_context.activity.from_property.name,
                    is_connect_chat_enabled=False
                )
            return

        # determine if it's a new chat session
        is_new_chat_session = True
        if self.is_new_chat_callback:
            is_new_chat_session = self.is_new_chat_callback(user_id=turn_context.activity.from_property.id)

        # if it's a new chat, Amazon connect will send a welcome message
        # we don't send any messages from activity hooks
        if is_new_chat_session:
            self.logger.debug("New chat session detected.  user_id: %s", turn_context.activity.from_property.id)
            # enable amazon connect chat invocation
            if self.set_data_callback:
                self.set_data_callback(
                    user_query=question,
                    user_id=turn_context.activity.from_property.id,
                    user_name=turn_context.activity.from_property.name,
                    is_connect_chat_enabled=True
                )
            return

        # check if the incoming message contains any ADAPTIVE_CARD_KEYWORDS
        if question.lower() in ADAPTIVE_CARD_KEYWORDS:
            await self.__send_adaptive_card(turn_context)
            # disable amazon connect chat invocation
            if self.set_data_callback:
                self.set_data_callback(
                    user_query=question,
                    user_id=turn_context.activity.from_property.id,
                    user_name=turn_context.activity.from_property.name,
                    is_connect_chat_enabled=False
                )
        # check if the incoming message matches any of DISCONNECT_KEYWORDS
        elif question.lower() in DISCONNECT_KEYWORDS:
            await turn_context.send_activity(DISCONNECT_MESSAGE)
            # disable amazon connect chat invocation and disconnect connect chat
            if self.set_data_callback:
                self.set_data_callback(
                    user_query=question,
                    user_id=turn_context.activity.from_property.id,
                    user_name=turn_context.activity.from_property.name,
                    is_connect_chat_enabled=True,
                    is_connect_chat_disconnected=True
                )
        else:
            await turn_context.send_activity(ACKNOWLEDGEMENT_MESSAGE)
            # enable amazon connect chat invocation
            if self.set_data_callback:
                self.set_data_callback(
                    user_query=question,
                    user_id=turn_context.activity.from_property.id,
                    user_name=turn_context.activity.from_property.name,
                    is_connect_chat_enabled=True
                )

    async def __send_adaptive_card(self, turn_context: TurnContext) -> Attachment:
        """
        Send Adaptive Card to the user
        """
        message = Activity(
            # text="Here is an Adaptive Card:",
            type=ActivityTypes.message,
            attachments=[self.__create_adaptive_card_attachment()],
        )

        await turn_context.send_activity(message)


    def __create_adaptive_card_attachment(self) -> Attachment:
        """
        Build FAQ adaptive card based on FAQ_LIST
        """
        card_data = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.6",
        }
        faq_heading = {
            "type": "TextBlock",
            "text": "Here are some commonly asked questions.",
            "wrap": True
        }
        container_items_list = []
        actions_list = []
        for i, question in enumerate(FAQ_LIST):

            if i % 2 == 0:
                action_item = {
                    "type": "Action.Submit",
                    "title": question,
                    "data": {
                        "button": question
                    }
                }
                actions_list.append(action_item)

            else:
                action_item = {
                    "type": "Action.Submit",
                    "title": question,
                    "data": {
                        "button": question
                    }
                }
                actions_list.append(action_item)

                # add action_list to item and append to to container_items_list
                item = {
                    "type": "ActionSet",
                    "actions": actions_list,
                }
                container_items_list.append(item)

                # reset actions_list
                actions_list = []

        # add last action_list to item and append to to container_items_list
        if len(actions_list) > 0:
            item = {
                "type": "ActionSet",
                "actions": actions_list,
            }
            container_items_list.append(item)

        container_items = {
            "type": "Container",
            "items": container_items_list
        }

        # build adaptive card
        body = [faq_heading, container_items]
        card_data["body"] = body

        return CardFactory.adaptive_card(card_data)
