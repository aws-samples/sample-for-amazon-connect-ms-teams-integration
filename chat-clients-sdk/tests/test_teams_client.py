# pylint: disable=import-error,unused-import
# hack to make sure we can import modules in ../src/** modules
try:
    import __setup__
except ModuleNotFoundError:
    import tests.__setup__
# end hack
# pylint: enable=import-error,unused-import

from unittest import IsolatedAsyncioTestCase
from chat_clients.teams.client import TeamsClient

class TestTeamsClient(IsolatedAsyncioTestCase):
    """TestTeamsClient"""

    def __init__(self, *args, **kwargs):
        super(TestTeamsClient, self).__init__(*args, **kwargs)

    def test_teams_event(self):
        """test_teams_event"""
        # set environment variable

        team_event_auth_token = "Bearer abc.abc.abc-abc-abc-abc-abc"
        teams_event_payload = {
            "text": "What can you tell me about Amazon?",
            "textFormat": "plain",
            "attachments": [
                {
                    "contentType": "text/html",
                    "content": "<p>What can you tell me about Amazon?</p>"
                }
            ],
            "type": "message",
            "timestamp": "2024-03-16T20:36:43.4785193Z",
            "localTimestamp": "2024-03-16T16:36:43.4785193-04:00",
            "id": "1710621403433",
            "channelId": "msteams",
            "serviceUrl": "https://smba.trafficmanager.net/ca/",
            "from": {
                "id": "29:1dHSuwj-p-abc-abc",
                "name": "Salman Moghal",
                "aadObjectId": "850a5427-f082-41fd-b4a9-2c6db3186d86"
            },
            "conversation": {
                "conversationType": "personal",
                "tenantId": "abc-3a66-4cc3-9b76-abc",
                "id": "a:1q-abc-abc"
            },
            "recipient": {
                "id": "28:abc-9b11-4566-a5e1-abc",
                "name": "connect-bot-1"
            },
            "entities": [
                {
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Mac",
                    "timezone": "America/Toronto",
                    "type": "clientInfo"
                }
            ],
            "channelData": {
                "tenant": {
                    "id": "abc-3a66-4cc3-9b76-abc"
                }
            },
            "locale": "en-US",
            "localTimezone": "America/Toronto"
        }
        client = TeamsClient(team_event_auth_token)
        response = client.send_message(teams_event_payload)

        # assert
        self.assertIsNotNone(response)
        self.assertEqual(response['status'], 201)
