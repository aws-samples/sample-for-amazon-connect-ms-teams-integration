"""lambda_function.py - lambda proxy for API Gateway resources"""
import json
from typing import Any, Dict
from time import time
from chat_clients.common.api_helper import build_response, build_error_response
from chat_clients.common.lambda_helper import show_lambda_stats
from chat_clients.common.logging_helper import get_logger
from api.slack import SlackApi
from api.teams import TeamsApi
from api.web import WebApi

# Configure logger
logger = get_logger(f"{__name__}")

# Lambda in-memory cache
cached_data = {
    "execution_time": time(),
    "invocation_count": 0,
}

def lambda_handler(event: Dict, context: Any):
    """This lambda function is a Lambda Proxy to API Gateway API. It
    processes REST API requests.  Following REST API calls are supported:

    1. POST /web

    When client invokes POST /web resource, the client must send JSON
    payload in HTTP POST request body.  The structure of the request is as
    follows:

    {
        "session_id": "abcd-efgh-1234",
        "user_name": "user1",
        "message": "user's text or query",
        "locale": "en_US", # "en_US" or "fr_CA" are only supported
    }

    Response to caller is a JSON object in the following format:

    {
        "session_id": "abcd-efgh-1234",
        "locale": "en_US", # "en_US" or "fr_CA" are only supported
        "message_id": "string", # message id from Amazon Connect
        "message_time": number, # The time when the message was sent  in ISO 8601 format
        "websocket_url": "string" # optional attribute
        "connection_expiry": "string" # The URL expiration timestamp in ISO date format.
    }

    2. POST /teams

    Azure Bot service invokes POST /teams resource.  The resource receives
    Azure Bot message.  Refer to Azure Bot documentation:

    Response sent to Azure Bot service is a JSON object in the following
    format:

    {
        "message_id": "string", # message id from Amazon Connect
        "message_timestamp": "string" # message time stamp from Amazon Connect
    }

    When error occurs during processing, the response is a JSON object
    in the following format:

    {
        "error_message": "string",
    }

    Args:
        event (Dict): API Gateway Lambda Proxy event
        context (Any): Lambda context object

    Returns:
        Dict: JSON response from the resource

    """

    # Lambda stats
    show_lambda_stats(event=event, context=context, cached_data=cached_data)

    if not event:
        return build_error_response(
            error_message="Unable to process request. Lambda proxy event is empty.",
            error_type="Bad Request")

    try:
        # extract method type and path from event
        http_method = event['httpMethod']
        path = event['path']

        # if method is POST and path is /slack, call SlackApi.process() method
        if http_method == "POST" and path == "/slack":
            payload: Dict = json.loads(event['body'])
            logger.debug("Received payload: %s", json.dumps(payload, indent=2))
            # gather attributes from chat_payload
            try:
                api = SlackApi(payload=payload)
                return build_response(api.process())
            except Exception as e:
                error_message = "Error: %s", str(e)
                logger.error(error_message)
                return build_error_response(
                    error_code=2,
                    error_message=error_message,
                    error_type="Bad Request",
                    status_code=400)

        # if method is POST and path is /teams, call TeamsApi.process() method
        if http_method == "POST" and path == "/teams":
            payload: Dict = json.loads(event['body'])
            auth_header: str = None
            if event.get('headers', None):
                auth_header = event.get('headers').get('Authorization', None)
                log_message = "Auth header is set" if auth_header else "Auth header is not set"
                logger.debug(log_message)
            logger.debug("Received payload: %s", json.dumps(payload, indent=2))
            # gather attributes from chat_payload
            try:
                api = TeamsApi(auth_header=auth_header, payload=payload)
                return build_response(api.process())
            except Exception as e:
                error_message = "Error: %s", str(e)
                logger.error(error_message)
                return build_error_response(
                    error_code=2,
                    error_message=error_message,
                    error_type="Bad Request",
                    status_code=400)

        # if method is POST and path is /web, call ChatApi.process() method
        elif http_method == "POST" and path == "/web":
            payload: Dict = json.loads(event['body'])
            logger.debug("Received payload: %s", json.dumps(payload, indent=2))
            # gather attributes from chat_payload
            try:
                session_id = payload['session_id']
                locale = payload['locale']
                user_name = payload['user_name']
                message = payload['message']
                api = WebApi(session_id=session_id, locale=locale, user_name=user_name)
                return build_response(api.process(message=message))
            except Exception as e:
                error_message = "Error: %s", str(e)
                logger.error(error_message)
                return build_error_response(
                    error_code=2,
                    error_message=error_message,
                    error_type="Bad Request",
                    status_code=400)

        # in all other cases, return 404 error
        return build_error_response(
                error_message=f"Invalid request.  http method: {http_method} , http path: {path}.",
                error_type="Bad Request",
                status_code=404)

    except Exception as e:
        error_message = "Error: %s", e
        logger.error(error_message)
        return build_error_response(
            error_code=2,
            error_message=error_message,
            error_type="Internal Server Error",
            status_code=500)
