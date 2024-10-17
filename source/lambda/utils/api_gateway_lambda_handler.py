#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
import traceback
from json import JSONDecodeError
from os import getenv
from typing import TypedDict, List

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from typing_extensions import NotRequired

from utils.decimal_json_encoder import DecimalJsonEncoder

APPLICATION_JSON = 'application/json'
ALLOWED_HEADERS = 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent'
default_headers = {
    'Access-Control-Allow-Headers': ALLOWED_HEADERS,
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': '*',
    'Content-Type': APPLICATION_JSON
}


class ApiGatewayResponse(TypedDict):
    statusCode: int
    body: NotRequired[str]
    headers: dict


class ResultListWrapper(TypedDict):
    Results: List


class AsynchronousResultListWrapper(ResultListWrapper):
    ScanInProgress: bool


class ClientException(Exception):
    def __init__(self, error: str, message: str, status_code: int = 400):
        self.error = error
        self.message = message
        self.status_code = status_code


def validate_content_type(event: dict):
    allowed_content_types = [
        'application/json',
        'application/json; charset=utf-8'
    ]
    content_type: str | None = None

    # Iterate through the headers and find the 'Content-Type' header (case-insensitive)
    for header_key, header_value in event["headers"].items():
        if header_key.lower() == 'content-type':
            content_type = header_value.lower()
            break

    if not content_type in allowed_content_types:
        raise ClientException(
            error='Invalid content-type',
            message=f'Accepting: {", ".join(allowed_content_types)}',
            status_code=415
        )


def validate_body(event: dict):
    if event.get("body"):
        validate_content_type(event)
        json.loads(event["body"])


class GenericApiGatewayEventHandler:

    def __init__(self):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))

    def handle_and_create_response(self,
                                   event: dict,
                                   context: LambdaContext,
                                   handler_function) -> ApiGatewayResponse:
        """
        Higher order function that takes a handler_function as an argument.
        The passed handler function does the business work, this function logs  and builds a response object for API Gateway.
        :param event: event from api gateway
        :param context: lambda context
        :param handler_function: the actual handler function to call
        """
        try:
            self.logger.debug(f"Event: {str(event)}")
            self.logger.debug(f"Context: {str(context)}")

            validate_body(event)

            event = APIGatewayProxyEvent(event)

            response_body = handler_function(event, context)

            if response_body or response_body == []:
                response_body_string = json.dumps(response_body, cls=DecimalJsonEncoder)
                self.logger.debug(f"Response Body: {response_body_string}")
                return {
                    'statusCode': 200,
                    'body': response_body_string,
                    'headers': default_headers,
                }
            else:
                return {
                    'statusCode': 204,
                    'headers': default_headers,
                }
        except ClientException as error:
            self.logger.error(f"Error: {error}")
            self.logger.error(traceback.format_exc())
            body = json.dumps({
                'Error': error.error,
                'Message': error.message
            })
            return {
                'statusCode': error.status_code,
                'body': body,
                'headers': default_headers,
            }
        except JSONDecodeError as error:
            self.logger.error(f"Error: {error}")
            self.logger.error(traceback.format_exc())
            body = json.dumps({
                'Error': 'JSONDecodeError',
                'Message': error.msg
            })
            return {
                'statusCode': 400,
                'body': body,
                'headers': default_headers,
            }
        except Exception as error:
            self.logger.error(f"Error: {error}")
            self.logger.error(traceback.format_exc())
            error_type = type(error).__name__
            body = {
                "Error": error_type,
                "Message": "An unexpected error occurred"
            }
            return {
                'statusCode': 500,
                'body': json.dumps(body),
                'headers': default_headers,
            }
