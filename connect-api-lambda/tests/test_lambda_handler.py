# pylint: disable=import-error,unused-import
# hack to make sure we can import modules in ../src/** modules
try:
    import __setup__
except ModuleNotFoundError:
    import tests.__setup__
# end hack
# pylint: enable=import-error,unused-import

from unittest import IsolatedAsyncioTestCase
import os
import json
from lambda_function import lambda_handler

context = {
    "invoked_function_arn": "arn:aws:lambda:us-east-1:1234567890:function:connect-api-lambda",
    "log_stream_name": "2023/07/04/[$LATEST]0068fba836c949aca5efc33da9ec57d3",
    "log_group_name": "/aws/lambda/connect-api-lambda",
    "aws_request_id": "610ed1be-2ce2-4e08-aa67-aa923aa7a750",
    "memory_limit_in_mb": "128",
    "remaining_time_in_millis": 3000
}

web_app_event = {
    "resource": "/web",
    "path": "/web",
    "httpMethod": "POST",
    "headers": {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Host": "api-1234567890.execute-api.us-east-1.amazonaws.com",
        "User-Agent": "PostmanRuntime/7.32.3",
        "X-Amzn-Trace-Id": "Root=1-64a48e27-7ec5e98776aa8cc075d7ab96",
        "X-Forwarded-For": "10.0.0.1",
        "X-Forwarded-Port": "443",
        "X-Forwarded-Proto": "https"
    },
    "multiValueHeaders": {
        "Accept": [
            "*/*"
        ],
        "Accept-Encoding": [
            "gzip, deflate, br"
        ],
        "Content-Type": [
            "application/json"
        ],
        "Host": [
            "api-1234567890.execute-api.us-east-1.amazonaws.com"
        ],
        "User-Agent": [
            "PostmanRuntime/7.32.3"
        ],
        "X-Amzn-Trace-Id": [
            "Root=1-64a48e27-7ec5e98776aa8cc075d7ab96"
        ],
        "X-Forwarded-For": [
            "10.0.0.1"
        ],
        "X-Forwarded-Port": [
            "443"
        ],
        "X-Forwarded-Proto": [
            "https"
        ]
    },
    "queryStringParameters": None,
    "multiValueQueryStringParameters": None,
    "pathParameters": None,
    "stageVariables": None,
    "requestContext": {
        "resourceId": "resource-1234567890",
        "resourcePath": "/chat",
        "httpMethod": "POST",
        "extendedRequestId": "HjsmQEz0oAMFutw=",
        "requestTime": "04/Jul/2023:21:24:55 +0000",
        "path": "/dev/chat",
        "accountId": "1234567890",
        "protocol": "HTTP/1.1",
        "stage": "dev",
        "domainPrefix": "api-1234567890",
        "requestTimeEpoch": 1688505895714,
        "requestId": "4f25adde-b235-4e15-99f2-6be5453a7c05",
        "identity": {
            "cognitoIdentityPoolId": None,
            "accountId": None,
            "cognitoIdentityId": None,
            "caller": None,
            "sourceIp": "10.0.0.1",
            "principalOrgId": None,
            "accessKey": None,
            "cognitoAuthenticationType": None,
            "cognitoAuthenticationProvider": None,
            "userArn": None,
            "userAgent": "PostmanRuntime/7.32.3",
            "user": None
        },
        "domainName": "api-1234567890.execute-api.us-east-1.amazonaws.com",
        "apiId": "api-1234567890"
    },
    "body": "{ \"session_id\": \"abcd-efgh-1234\", \"user_name\": \"user1\", \"message\": \"Hello, How are you?\", \"locale\": \"en_US\" }",
    "isBase64Encoded": False
}

slack_event = {
    "resource": "/slack",
    "path": "/slack",
    "httpMethod": "POST",
    "headers": {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Host": "api-1234567890.execute-api.us-east-1.amazonaws.com",
        "User-Agent": "PostmanRuntime/7.32.3",
        "X-Amzn-Trace-Id": "Root=1-64a48e27-7ec5e98776aa8cc075d7ab96",
        "X-Forwarded-For": "10.0.0.1",
        "X-Forwarded-Port": "443",
        "X-Forwarded-Proto": "https"
    },
    "multiValueHeaders": {
        "Accept": [
            "*/*"
        ],
        "Accept-Encoding": [
            "gzip, deflate, br"
        ],
        "Content-Type": [
            "application/json"
        ],
        "Host": [
            "api-1234567890.execute-api.us-east-1.amazonaws.com"
        ],
        "User-Agent": [
            "PostmanRuntime/7.32.3"
        ],
        "X-Amzn-Trace-Id": [
            "Root=1-64a48e27-7ec5e98776aa8cc075d7ab96"
        ],
        "X-Forwarded-For": [
            "10.0.0.1"
        ],
        "X-Forwarded-Port": [
            "443"
        ],
        "X-Forwarded-Proto": [
            "https"
        ]
    },
    "queryStringParameters": None,
    "multiValueQueryStringParameters": None,
    "pathParameters": None,
    "stageVariables": None,
    "requestContext": {
        "resourceId": "resource-1234567890",
        "resourcePath": "/chat",
        "httpMethod": "POST",
        "extendedRequestId": "HjsmQEz0oAMFutw=",
        "requestTime": "04/Jul/2023:21:24:55 +0000",
        "path": "/dev/chat",
        "accountId": "1234567890",
        "protocol": "HTTP/1.1",
        "stage": "dev",
        "domainPrefix": "api-1234567890",
        "requestTimeEpoch": 1688505895714,
        "requestId": "4f25adde-b235-4e15-99f2-6be5453a7c05",
        "identity": {
            "cognitoIdentityPoolId": None,
            "accountId": None,
            "cognitoIdentityId": None,
            "caller": None,
            "sourceIp": "10.0.0.1",
            "principalOrgId": None,
            "accessKey": None,
            "cognitoAuthenticationType": None,
            "cognitoAuthenticationProvider": None,
            "userArn": None,
            "userAgent": "PostmanRuntime/7.32.3",
            "user": None
        },
        "domainName": "api-1234567890.execute-api.us-east-1.amazonaws.com",
        "apiId": "api-1234567890"
    },
    "body": "",
    "isBase64Encoded": False
}

teams_event = {
    "resource": "/teams",
    "path": "/teams",
    "httpMethod": "POST",
    "headers": {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Authorization": "Bearer abcd",
        "Content-Type": "application/json",
        "Host": "api-1234567890.execute-api.us-east-1.amazonaws.com",
        "User-Agent": "PostmanRuntime/7.32.3",
        "X-Amzn-Trace-Id": "Root=1-64a48e27-7ec5e98776aa8cc075d7ab96",
        "X-Forwarded-For": "20.42.0.64, 161.69.116.11",
        "X-Forwarded-Port": "443",
        "X-Forwarded-Proto": "https",
        "x-ms-conversation-id": "HJsiQmPpj5U1OQpAhCRZjm-us"
    },
    "multiValueHeaders": {
        "Accept": [
            "*/*"
        ],
        "Accept-Encoding": [
            "gzip, deflate, br"
        ],
        "Authorization":
        [
            "Bearer abcd"
        ],
        "channelid":
        [
            "msteams"
        ],
        "Content-Type": [
            "application/json"
        ],
        "Host": [
            "api-1234567890.execute-api.us-east-1.amazonaws.com"
        ],
        "User-Agent": [
            "PostmanRuntime/7.32.3"
        ],
        "X-Amzn-Trace-Id": [
            "Root=1-64a48e27-7ec5e98776aa8cc075d7ab96"
        ],
        "X-Forwarded-Port": [
            "443"
        ],
        "X-Forwarded-Proto": [
            "https"
        ],
        "X-Forwarded-For":
        [
            "20.42.0.64, 161.69.116.11"
        ],
        "x-ms-conversation-id":
        [
            "HJsiQmPpj5U1OQpAhCRZjm-us"
        ]
    },
    "queryStringParameters": None,
    "multiValueQueryStringParameters": None,
    "pathParameters": None,
    "stageVariables": None,
    "requestContext": {
        "resourceId": "resource-1234567890",
        "resourcePath": "/chat",
        "httpMethod": "POST",
        "extendedRequestId": "HjsmQEz0oAMFutw=",
        "requestTime": "04/Jul/2023:21:24:55 +0000",
        "path": "/dev/chat",
        "accountId": "1234567890",
        "protocol": "HTTP/1.1",
        "stage": "dev",
        "domainPrefix": "api-1234567890",
        "requestTimeEpoch": 1688505895714,
        "requestId": "4f25adde-b235-4e15-99f2-6be5453a7c05",
        "identity": {
            "cognitoIdentityPoolId": None,
            "accountId": None,
            "cognitoIdentityId": None,
            "caller": None,
            "sourceIp": "10.0.0.1",
            "principalOrgId": None,
            "accessKey": None,
            "cognitoAuthenticationType": None,
            "cognitoAuthenticationProvider": None,
            "userArn": None,
            "userAgent": "PostmanRuntime/7.32.3",
            "user": None
        },
        "domainName": "api-1234567890.execute-api.us-east-1.amazonaws.com",
        "apiId": "api-1234567890"
    },
    "body": "",
    "isBase64Encoded": False
}

class TestConnectApiLambda(IsolatedAsyncioTestCase):
    """TestConnectApiLambda"""

    def __init__(self, *args, **kwargs):
        super(TestConnectApiLambda, self).__init__(*args, **kwargs)

    def test_lambda_function_slack_url_verification_event(self):
        """test_lambda_function_slack_url_verification_event"""
        # set environment variable
        os.environ['USER_CHAT_CLIENT_TYPE'] = 'SLACK'

        challenge_token = "abcd12342rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7tYXAYM8P"
        url_verification_payload = {
            "token": "Jhj5dZrVaK7ZwHHjRyZWjbDl",
            "challenge": challenge_token,
            "type": "url_verification"
        }
        body = json.dumps(url_verification_payload)
        slack_event['body'] = body
        response = lambda_handler(slack_event, context)

        # assert
        self.assertIsNotNone(response)
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['challenge'], challenge_token)

    def test_lambda_function_slack_im_event(self):
        """test_lambda_function_slack_im_event"""
        # set environment variable
        os.environ['USER_CHAT_CLIENT_TYPE'] = 'SLACK'

        im_event_payload = {
            "token": "XXXXXXXXXXXXXXXXXXXXXXXX",
            "team_id": "XXXXX",
            "context_team_id": "YYYYYYYYYYYYYYYYYYYY",
            "context_enterprise_id": None,
            "api_app_id": "XXXXX",
            "event": {
                "client_msg_id": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "type": "message",
                "text": "Hello world",
                "user": "ABCDEFGH0",
                "ts": "1688505896.002700",
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
                                        "text": "Hello world"
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "team": "T0001",
                "channel": "C2147483705",
                "event_ts": "1688505896.002700",
                "channel_type": "im"
            },
            "type": "event_callback",
            "event_id": "XXXXXX",
            "event_time": 1688505896,
            "authorizations": [
                {
                    "enterprise_id": None,
                    "team_id": "XXXXX",
                    "user_id": "EFGH5678",
                    "is_bot": True,
                    "is_enterprise_install": False
                }
            ],
            "is_ext_shared_channel": False,
            "event_context": "4-ABCDEF"
        }
        body = json.dumps(im_event_payload)
        slack_event['body'] = body
        response = lambda_handler(slack_event, context)

        # assert
        self.assertIsNotNone(response)
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        # verify that body contains an attribute 'id'
        self.assertIsNotNone(body['message_id'])
        self.assertIsNotNone(body['message_timestamp'])

    def test_lambda_function_teams_event(self):
        """test_lambda_function_teams_event"""
        # set environment variable
        os.environ['USER_CHAT_CLIENT_TYPE'] = "TEAMS"
        team_event_auth_token = "Bearer abcd123STJ4V2ZjZW9JU2FxZ3pFV3l5YyIsIng1dCI6Ii1LM0JhUVJvSTJ4V2ZjZW9JU2FxZ3pFV3l5YyIsInR5cCI6IkpXVCJ9.ew0KICAic2VydmljZXVybCI6ICJodHRwczovL3NtYmEudHJhZmZpY21hbmFnZXIubmV0L2luLzkyYTg5ZGMzLTJiMTktNDUxMi05ZTE0LTZkNmZhZjAyNTcyNy8iLA0KICAibmJmIjogMTczNzQ0OTIwOSwNCiAgImV4cCI6IDE3Mzc0NTI4MDksDQogICJpc3MiOiAiaHR0cHM6Ly9hcGkuYm90ZnJhbWV3b3JrLmNvbSIsDQogICJhdWQiOiAiNDc3ZWQ1NDUtNmJlMi00OGQ4LWE2OWItZGMzZWRkZTEzNjQ1Ig0KfQ.HOUFHvPpiGhXo62RAOmTah_8awz7f2WjqRsEfhYf5iE-t6qg71jylmnzeLdY03GSny8Cv_gZnNqLX935T4JY049ep5mTWM9bm7uNPCz-YTjWcTPlFwAovK2Q0MyixctY5VDoRyq3HsH_pb6WEdzucPgTod_NNWDqZa34OrtsPWruovCLEvbCmEru0-BQAXU0C4pzO4Jxnum2z2vKxrBk_qLOiD4IT5y8X_G3r-HK7EqtTA9qTLDajTyyK9S4T6Rs2sCNxliANSrIxbsXWGgftdi-9h-hta4qlMlVttpqPh--ig-KRmo3_9Q5daQSll3B_5I2sGfDbFU52ZuMlI64dA"

        teams_event_payload = {
            "text": "Connect me to an agent",
            "textFormat": "plain",
            "attachments": [
                {
                    "contentType": "text/html",
                    "content": "<p>Hello!</p>"
                }
            ],
            "type": "message",
            "timestamp": "2025-01-16T08:21:32.3243018Z",
            "localTimestamp": "2025-01-16T13:51:32.3243018+05:30",
            "id": "1737015692303",
            "channelId": "msteams",
            "serviceUrl": "https://smba.trafficmanager.net/in/92a89dc3-2b19-4512-9e14-6d6faf025727/",
            "from": {
                "id": "29:1S6rGA-Q6tQTtsRLjejJC_F36Euy_dyqq9exMgY8vrdAKuzkeiZthO_BNIfmyMCOzApmfNaD1gXGMurGHmaWKIg",
                "name": "Pratik Sharma",
                "aadObjectId": "538651c3-f264-4f88-822a-51916fa9a53e"
            },
            "conversation": {
                "conversationType": "personal",
                "tenantId": "92a89dc3-2b19-4512-9e14-6d6faf025727",
                "id": "a:abcd123XOC4fDKPDcks9zniDi3UWpfgk5VUOBp6x3xhVSdP7RwznZFDixOsDgvbphA5z9p3FQ3EdpaJRCrFvjOgkKIneAqbVNr9Wa3-ESso9ru4cff"
            },
            "recipient": {
                "id": "28:77200b57-12ee-49a4-8260-bc002b57169f",
                "name": "connect-bot"
            },
            "entities": [
                {
                    "locale": "en-US",
                    "country": "US",
                    "platform": "Web",
                    "timezone": "Asia/Kolkata",
                    "type": "clientInfo"
                }
            ],
            "channelData": {
                "tenant": {
                    "id": "92a89dc3-2b19-4512-9e14-6d6faf025727"
                }
            },
            "locale": "en-US",
            "localTimezone": "Asia/Kolkata"
        }
        body = json.dumps(teams_event_payload)
        teams_event['body'] = body
        teams_event['headers']['Authorization'] = team_event_auth_token
        teams_event['multiValueHeaders']['Authorization'] = [team_event_auth_token]
        response = lambda_handler(teams_event, context)

        # assert
        self.assertIsNotNone(response)
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        # verify that body contains an attribute 'id'
        self.assertIsNotNone(body['status'])

    def test_lambda_function_teams_adaptive_card_event(self):
        """test_lambda_function_teams_adaptive_card_event"""
        # set environment variable
        os.environ['USER_CHAT_CLIENT_TYPE'] = "TEAMS"

        team_event_auth_token = "Bearer abc.abc.abc-abc-abc-abc-abc"
        teams_event_payload = {
            "type": "message",
            "timestamp": "2024-03-19T09:00:04.022Z",
            "localTimestamp": "2024-03-19T05:00:04.022-04:00",
            "id": "f:9c5ff46f-cc34-c07b-2531-4633178f2317",
            "channelId": "msteams",
            "serviceUrl": "https://smba.trafficmanager.net/ca/",
            "from": {
                "id": "29:1234567-p-T7mM9d8z2woZI7F6W6Vo-X7ihRkczXHutouEs1Bgy71k-HocRtAVgjYZsHGUB3TlT6Bv49bxglBJA",
                "name": "Salman Moghal",
                "aadObjectId": "850a5427-f082-41fd-b4a9-2c6db3186d86"
            },
            "conversation": {
                "conversationType": "personal",
                "tenantId": "12345678-3a66-4cc3-9b76-83bde29d3e62",
                "id": "a:abcd123EyPvI06wVdaiboD1L9lK2QJEVEIxZco8XCWdZlIRGbTXnin-sUFXB5AVK3VYXSKxVzs9BQFY7N_ER2ou_DBCjooQkIEXMEPTvrZlw4a0z0RIadi4ohiAcmGr"
            },
            "recipient": {
                "id": "28:12345678-9b11-4566-a5e1-db69dbb06e9f",
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
                    "id": "12345678-3a66-4cc3-9b76-83bde29d3e62"
                }
            },
            "locale": "en-US",
            "localTimezone": "America/Toronto"
        }
        body = json.dumps(teams_event_payload)
        teams_event['body'] = body
        teams_event['headers']['Authorization'] = team_event_auth_token
        teams_event['multiValueHeaders']['Authorization'] = [team_event_auth_token]
        response = lambda_handler(teams_event, context)

        # assert
        self.assertIsNotNone(response)
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        # verify that body contains an attribute 'id'
        self.assertIsNotNone(body['status'])

    def test_lambda_function_teams_disconnect_event(self):
        """test_lambda_function_teams_adaptive_card_event"""
        # set environment variable
        os.environ['USER_CHAT_CLIENT_TYPE'] = "TEAMS"

        team_event_auth_token = "Bearer abc.abc.abc-abc-abc-abc-abc"
        teams_event_payload = {
            "text": "disconnect",
            "textFormat": "plain",
            "attachments": [
                {
                    "contentType": "text/html",
                    "content": "<p>disconnect</p>"
                }
            ],
            "type": "message",
            "timestamp": "2024-03-25T17:19:50.3969802Z",
            "localTimestamp": "2024-03-25T13:19:50.3969802-04:00",
            "id": "1711387190347",
            "channelId": "msteams",
            "serviceUrl": "https://smba.trafficmanager.net/ca/",
            "from": {
                "id": "29:abcd123-p-T7mM9d8z2woZI7F6W6Vo-X7ihRkczXHutouEs1Bgy71k-HocRtAVgjYZsHGUB3TlT6Bv49bxglBJA",
                "name": "Salman Moghal",
                "aadObjectId": "850a5427-f082-41fd-b4a9-2c6db3186d86"
            },
            "conversation": {
                "conversationType": "personal",
                "tenantId": "12345678-3a66-4cc3-9b76-83bde29d3e62",
                "id": "a:abcd123daiboD1L9lK2QJEVEIxZco8XCWdZlIRGbTXnin-sUFXB5AVK3VYXSKxVzs9BQFY7N_ER2ou_DBCjooQkIEXMEPTvrZlw4a0z0RIadi4ohiAcmGr"
            },
            "recipient": {
                "id": "28:12345678-9b11-4566-a5e1-db69dbb06e9f",
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
                    "id": "12345678-3a66-4cc3-9b76-83bde29d3e62"
                }
            },
            "locale": "en-US",
            "localTimezone": "America/Toronto"
        }
        body = json.dumps(teams_event_payload)
        teams_event['body'] = body
        teams_event['headers']['Authorization'] = team_event_auth_token
        teams_event['multiValueHeaders']['Authorization'] = [team_event_auth_token]
        response = lambda_handler(teams_event, context)

        # assert
        self.assertIsNotNone(response)
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        # verify that body contains an attribute 'id'
        self.assertIsNotNone(body['status'])

    def test_lambda_function_web_event(self):
        """test_lambda_function_web_event"""
        # set environment variable
        os.environ['USER_CHAT_CLIENT_TYPE'] = 'WEB'
        response = lambda_handler(web_app_event, context)

        # assert
        self.assertIsNotNone(response)
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        # verify that body contains required response attributes
        self.assertIsNotNone(body['message_id'])
        self.assertIsNotNone(body['message_timestamp'])
