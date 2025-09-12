"""echo_bot.py - This module contains class that implements a simple echo bot."""
from botbuilder.core import (
    TurnContext,
    ActivityHandler
)
from botbuilder.schema import ChannelAccount

class EchoBot(ActivityHandler):
    """
    See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.
    """

    async def on_message_activity(self, turn_context: TurnContext):
        """on_message_activity"""
        await turn_context.send_activity(f"You said '{ turn_context.activity.text }'")

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        """on_members_added_activity"""
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(f"Hello and welcome {member_added.name}!")

