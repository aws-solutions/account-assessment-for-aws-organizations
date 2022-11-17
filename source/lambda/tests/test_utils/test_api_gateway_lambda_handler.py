# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools.utilities.typing import LambdaContext

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
    response = GenericApiGatewayEventHandler().handle_and_create_response(event, LambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 200
    assert response['body'] == '{"foo": "bar"}'


def test_wraps_handler_error_in_http_response():
    # ARRANGE
    def handler_function(_event, _context):
        raise ClientException(error='Some error', message='The handler function threw an error', status_code=400)

    # ACT
    response = GenericApiGatewayEventHandler().handle_and_create_response({}, LambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 400
    assert response['body'] == '{"Error": "Some error", "Message": "The handler function threw an error"}'


def test_wraps_handler_exception_in_http_response():
    # ARRANGE
    def handler_function(_event, _context):
        raise IndexError()

    # ACT
    response = GenericApiGatewayEventHandler().handle_and_create_response({}, LambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 500
    assert response['body'] == '{"Error": "IndexError", "Message": "An unexpected error occurred"}'


def test_returns_415_on_missing_content_type():
    # ARRANGE
    def handler_function(_event, _context):
        raise IndexError()

    event = {
        'body': '{}',
        'headers': {}
    }

    # ACT
    response = GenericApiGatewayEventHandler().handle_and_create_response(event, LambdaContext(), handler_function)

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
    response = GenericApiGatewayEventHandler().handle_and_create_response(event, LambdaContext(), handler_function)

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
    response = GenericApiGatewayEventHandler().handle_and_create_response(event, LambdaContext(), handler_function)

    # ASSERT
    assert response['statusCode'] == 400
