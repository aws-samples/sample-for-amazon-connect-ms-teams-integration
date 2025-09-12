"""lambda_handler.py:

    This module contains the lambda entry point function, `lambda_handler`.
    Lambda function is configured as a subscription to SNS topic.  It processes
    SNS records and calls callback API to send messages to target user.

    Following backend

    Refer to blueprint-api-connect-lambda that calls Amazon Connect service to
    initiate SNS invocation.

    This function uses also looks up the data inbound in SNS message in DynamoDB
    to correlate response from Amazon Connect and target Slack user.
"""
import json
from time import time
from chat_clients.common.logging_helper import get_logger
from chat_clients.common.lambda_helper import show_lambda_stats
from sns.sns_helper import SNS

# Configure logger
logger = get_logger(f"{__name__}")

# Lambda in-memory cache
cached_data = {
    "execution_time": time(),
    "invocation_count": 0
}

def lambda_handler(event, context):
    """lambda handler that processes messages from SNS service.  SNS
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

    Args:
        event (dict): SNS event
        context (dict): Lambda context object

    Returns:
        response (dict): Returns a success message

    Throws:
        Throws an exception if there is an error during processing.
        The exception message is logged in the CloudWatch logs.
    """

    # Lambda stats
    # show_lambda_stats(event=event, context=context, cached_data=cached_data)

    try:
        json.dumps(event)
        sns = SNS(event)
        response = sns.process()
        return response
    except Exception as e:
        error_message = "Failed to process SNS message: " + str(e)
        logger.error(error_message)
        raise Exception(error_message) from e
