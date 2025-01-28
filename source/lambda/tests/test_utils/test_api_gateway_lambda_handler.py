#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

from tests.test_utils.testdata_factory import TestLambdaContext
from utils.api_gateway_lambda_handler import GenericApiGatewayEventHandler, ClientException


def test_wraps_handler_response_in_http_response():
    # ARRANGE
    def handler_function(_event, _context):
        return {"foo": "bar"}

    event = {
        'body': '{}',
        'headers': {
            'content-type': 'application/json'
        }
    }

    # ACT
    response = GenericApiGatewayEventHandler().handle_and_create_response(event, TestLambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 200
    assert response['body'] == '{"foo": "bar"}'


def test_accepts_content_type_case_insensitive():
    # ARRANGE
    def handler_function(_event, _context):
        return {"foo": "bar"}

    event = {
        'body': '{}',
        'headers': {
            'Content-type': 'application/json; charset=UTF-8'
        }
    }

    # ACT
    response = GenericApiGatewayEventHandler().handle_and_create_response(event, TestLambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 200
    assert response['body'] == '{"foo": "bar"}'


def test_returns_415_on_missing_header():
    # ARRANGE
    def handler_function(_event, _context):
        raise IndexError()

    event = {
        'body': '{invalid_syntax}',
        'headers': {
            # content-type header is missing
        }
    }

    # ACT
    response = GenericApiGatewayEventHandler().handle_and_create_response(event, TestLambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 415


def test_wraps_handler_error_in_http_response():
    # ARRANGE
    def handler_function(_event, _context):
        raise ClientException(error='Some error', message='The handler function threw an error', status_code=400)

    # ACT
    response = GenericApiGatewayEventHandler().handle_and_create_response({}, TestLambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 400
    assert response['body'] == '{"Error": "Some error", "Message": "The handler function threw an error"}'


def test_wraps_handler_exception_in_http_response():
    # ARRANGE
    def handler_function(_event, _context):
        raise IndexError() # some unexpected error that is not specifically handled. should be caught by the generic catch clause

    # ACT
    response = GenericApiGatewayEventHandler().handle_and_create_response({}, TestLambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 400
    payload = json.loads(response['body'])
    assert payload['Error'] == 'IndexError'
    assert payload['Message'] == 'An unexpected error occurred. Inspect CloudWatch logs for more information.'


def test_returns_415_on_missing_content_type():
    # ARRANGE
    def handler_function(_event, _context):
        raise IndexError()

    event = {
        'body': '{}',
        'headers': {}
    }

    # ACT
    response = GenericApiGatewayEventHandler().handle_and_create_response(event, TestLambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 415


def test_returns_415_on_invalid_content_type():
    # ARRANGE
    def handler_function(_event, _context):
        raise IndexError()

    event = {
        'body': '{}',
        'headers': {
            'content-type': 'application/xml'
        }
    }

    # ACT
    response = GenericApiGatewayEventHandler().handle_and_create_response(event, TestLambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 415


def test_returns_400_on_invalid_json_body():
    # ARRANGE
    def handler_function(_event, _context):
        raise IndexError()

    event = {
        'body': '{invalid_syntax}',
        'headers': {
            'content-type': 'application/json'
        }
    }

    # ACT
    response = GenericApiGatewayEventHandler().handle_and_create_response(event, TestLambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 400


def test_content_type_should_be_case_insensitive():
    # ARRANGE
    def handler_function(_event, _context):
        return {"foo": "bar"}

    event = {
        'body': '{}',
        'headers': {
            'Content-Type': 'application/json'
        }
    }

    # ACT
    response = GenericApiGatewayEventHandler().handle_and_create_response(event, TestLambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 200

    event = {
        'body': '{}',
        'headers': {
            'ConTent-Type': 'application/json'
        }
    }

    # ACT
    response = GenericApiGatewayEventHandler().handle_and_create_response(event, TestLambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 200

    event = {
        'body': '{}',
        'headers': {
            'CONTENT-TYPE': 'application/json'
        }
    }

    # ACT
    response = GenericApiGatewayEventHandler().handle_and_create_response(event, TestLambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 200
