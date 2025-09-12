"""test_adaptive_card.py - Adaptive Card unit tests"""
# hack to make sure we can import modules in ../src/** modules
# pylint: disable=import-error,unused-import
try:
    import __setup__
except ModuleNotFoundError:
    import tests.__setup__
# end hack
# pylint: enable=import-error,unused-import

import unittest

FAQ_LIST = [
    "Who is the CEO  of Mondelez International?",
    "How did Amazon perform based on annual report?",
    "Among competitors, have there been any major mergers, acquisitions, or corporate actions for Mondelez International Inc.?",
    "What are challenges faced by Mondelez International Inc.?",
    "What can you tell me about NVIDIA quarterly results"
]

class TestAdaptiveCard(unittest.TestCase):
    """TestAdaptiveCard"""
    def __init__(self, *args, **kwargs):
        super(TestAdaptiveCard, self).__init__(*args, **kwargs)

    def test_adaptive_card(self):
        """test_adaptive_card"""
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

        # assert
        self.assertIsNotNone(card_data)
