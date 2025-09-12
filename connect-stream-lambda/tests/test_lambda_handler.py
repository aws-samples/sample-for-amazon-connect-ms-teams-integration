# pylint: disable=import-error,unused-import
# hack to make sure we can import modules in ../src/** modules
try:
    import __setup__
except ModuleNotFoundError:
    import tests.__setup__
# end hack
# pylint: enable=import-error,unused-import

import unittest
from lambda_function import lambda_handler


class TestConnectStreamLambda(unittest.TestCase):
    """TestConnectStreamLambda"""

    def __init__(self, *args, **kwargs):
        super(TestConnectStreamLambda, self).__init__(*args, **kwargs)

        # context
        self.context = 1

        # event
        self.sns_event = {
            "Records": [
                {
                    "EventSource": "aws:sns",
                    "EventVersion": "1.0",
                    "EventSubscriptionArn": "arn:aws:sns:us-west-2:ACCOUNT_ID:CONNECT_STREAM:db21221e-f910-4b02-b524-c51cdf266149",
                    "Sns": {
                        "Type": "Notification",
                        "MessageId": "0f010edf-8ed5-5c87-8313-50ab3ead8e4e",
                        "TopicArn": "arn:aws:sns:us-east-1:ACCOUNT_ID:connect_stream_topic",
                        "Subject": None,
                        "Message": "{\"AbsoluteTime\":\"2024-03-20T09:36:56.174Z\",\"Content\":\"Hello, thanks for contacting us. This is an example of what the Amazon Connect virtual contact center can enable you to do.\",\"ContentType\":\"text/plain\",\"Id\":\"00c35ebd-8d20-4f88-9aa6-68bf556b395f\",\"Type\":\"MESSAGE\",\"ParticipantId\":\"98c5ee0b-f9d1-4539-909e-b5352093a9e5\",\"DisplayName\":\"SYSTEM_MESSAGE\",\"ParticipantRole\":\"SYSTEM\",\"InitialContactId\":\"1e760cb3-4899-46aa-a937-804d70e15230\",\"ContactId\":\"1e760cb3-4899-46aa-a937-804d70e15230\"}",
                        "Timestamp": "2024-03-20T09:36:56.236Z",
                        "SignatureVersion": "1",
                        "Signature": "abcd123luItI6FMG2e/ky0gj5zOTxTT==",
                        "SigningCertUrl": "https://sns.us-west-2.amazonaws.com/SimpleNotificationService-60eadc530605d63b8e62a523676ef735.pem",
                        "UnsubscribeUrl": "https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:ACCOUNT_ID:CONNECT_STREAM:db21221e-f910-4b02-b524-c51cdf266149",
                        "MessageAttributes": {
                            "InitialContactId": {
                                "Type": "String",
                                "Value": "1e760cb3-4899-46aa-a937-804d70e15230"
                            },
                            "MessageVisibility": {
                                "Type": "String",
                                "Value": "ALL"
                            },
                            "Type": {
                                "Type": "String",
                                "Value": "MESSAGE"
                            },
                            "AccountId": {
                                "Type": "String",
                                "Value": "ACCOUNT_ID"
                            },
                            "ContentType": {
                                "Type": "String",
                                "Value": "text/plain"
                            },
                            "InstanceId": {
                                "Type": "String",
                                "Value": "c800978e-fdc0-406e-bbb0-4f575f5842a6"
                            },
                            "ContactId": {
                                "Type": "String",
                                "Value": "1e760cb3-4899-46aa-a937-804d70e15230"
                            },
                            "ParticipantRole": {
                                "Type": "String",
                                "Value": "SYSTEM"
                            }
                        }
                    }
                }
            ]
        }

        # event 2
        self.sns_agent_disconnect_event = {
            "Records": [
                {
                    "EventSource": "aws:sns",
                    "EventVersion": "1.0",
                    "EventSubscriptionArn": "arn:aws:sns:us-west-2:ACCOUNT_ID:CONNECT_STREAM:db21221e-f910-4b02-b524-c51cdf266149",
                    "Sns": {
                        "Type": "Notification",
                        "MessageId": "3320f26b-0fc1-5417-9a18-ac1fb4b1c779",
                        "TopicArn": "arn:aws:sns:us-east-1:ACCOUNT_ID:connect_stream_topic",
                        "Subject": None,
                        "Message": "{\"AbsoluteTime\":\"2024-03-20T10:23:43.987Z\",\"Content\":\"The agent has disconnected. If the customer sends a message in the next 15 minutes, the chat will pick up where it left off.\",\"ContentType\":\"text/plain\",\"Id\":\"265ecf8b-113f-4246-86c2-b6c3b3666667\",\"Type\":\"MESSAGE\",\"ParticipantId\":\"ac3a13ef-49e9-414e-acef-a1f3441a1445\",\"DisplayName\":\"SYSTEM_MESSAGE\",\"ParticipantRole\":\"SYSTEM\",\"InitialContactId\":\"00ed6f5e-4d27-4618-84f7-607c077dfe0f\",\"ContactId\":\"1e760cb3-4899-46aa-a937-804d70e15230\"}",
                        "Timestamp": "2024-03-20T10:23:44.040Z",
                        "SignatureVersion": "1",
                        "Signature": "abcd123D3AmESi06f9L/7zXma47a6mt4s64mYItpReMPqHxJsiG1l1VeJ/hCrxr70h5mZFghOgNozQd9kBAcA74nwoF4CVWg6fVEF17gZyMX8LS1Z/KBTOc4Ls9EWj7u3CCpvxP/vEmc9mAJJuGrmaGj+R3DLFiVukcFe0WC/RDqad9ouHbZf6ou3yy1SmxHpuxsMQwwEqmjQo8JMc84Nz/Osx38tFvws24E+00+HOcr7o4Wp5YBPuxB0dvj8qYfHRXveXviXm6NGq1Dnxeq1Fol4ICy0nGDpucHnLOxjlD5WHkReKwisEUdb+fB4YeWM1iKN6I5A==",
                        "SigningCertUrl": "https://sns.us-west-2.amazonaws.com/SimpleNotificationService-60eadc530605d63b8e62a523676ef735.pem",
                        "UnsubscribeUrl": "https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:ACCOUNT_ID:CONNECT_STREAM:db21221e-f910-4b02-b524-c51cdf266149",
                        "MessageAttributes": {
                            "InitialContactId": {
                                "Type": "String",
                                "Value": "00ed6f5e-4d27-4618-84f7-607c077dfe0f"
                            },
                            "MessageVisibility": {
                                "Type": "String",
                                "Value": "ALL"
                            },
                            "Type": {
                                "Type": "String",
                                "Value": "MESSAGE"
                            },
                            "AccountId": {
                                "Type": "String",
                                "Value": "ACCOUNT_ID"
                            },
                            "ContentType": {
                                "Type": "String",
                                "Value": "text/plain"
                            },
                            "InstanceId": {
                                "Type": "String",
                                "Value": "c800978e-fdc0-406e-bbb0-4f575f5842a6"
                            },
                            "ContactId": {
                                "Type": "String",
                                "Value": "fc367a2e-79d0-4a9b-a8b9-d312db02054c"
                            },
                            "ParticipantRole": {
                                "Type": "String",
                                "Value": "SYSTEM"
                            }
                        }
                    }
                }
            ]
        }

    def test_lambda_function(self):
        """test_lambda_function"""

        response = lambda_handler(self.sns_event, self.context)
        self.assertIsNotNone(response)

        # assert
        self.assertIsNotNone(response)

    def test_lambda_function_agent_disconnect(self):
        """test_lambda_function_agent_disconnect"""

        response = lambda_handler(self.sns_agent_disconnect_event, self.context)
        self.assertIsNotNone(response)

        # assert
        self.assertIsNotNone(response)
