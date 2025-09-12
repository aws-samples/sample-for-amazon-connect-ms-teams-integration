"""utils.api_helper.py - common REST api helper functions"""
import json
from typing import Dict
from chat_clients.common.logging_helper import get_logger

# Configure logger
logger = get_logger(f"{__name__}")

BASE_HEADERS = {
  'Access-Control-Allow-Headers':
    'Content-Type,X-Amz-Date,Authorization,identification,X-Api-Key,X-Amz-Security-Token',
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
}

def build_response(body: Dict, status_code: int = 200) -> Dict:
    """build_response - builds a response object for the api

    Args:
        body (dict): response body
        status_code (int): http status code

    Returns:
        dict: response object
    """
    return {
        'statusCode': status_code,
        'headers': BASE_HEADERS,
        'body': json.dumps(body)
    }

def build_error_response(error_code:int=1, error_message: str="Bad Request", error_type:str=None, status_code:int=400) -> Dict:
    """build_error_response - builds an error response object for the api

    Args:
        error_code (int): error code
        error_message (str): error message
        error_type (str): error type
        status_code (int): http status code

    Returns:
        dict: response object
    """
    logger.error("Error code: %d, Error message: %s", error_code, error_message)
    logger.error("Error type: %s", error_type)
    logger.error("Status code: %d", status_code)

    # Build error response object
    # Ref: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    # error_type is optional, if not provided, default to 'Error'
    if not error_type:
        error_type = 'Error'

    # error_message is required, if not provided, default to 'Internal Server Error'
    if not error_message:
        error_message = 'Internal Server Error'

    # error_code is required, if not provided, default to 500
    if not error_code:
        error_code = 500

    # Build error response object
    error_response = {
        'error': {
            'code': error_code,
            'message': error_message,
            'type': error_type
            }
        }

    return build_response(error_response, status_code)
