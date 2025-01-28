#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import boto3
from moto import mock_aws

from manage_cognito_domain.manage_cognito_domain import lambda_handler
from tests.test_utils.testdata_factory import TestLambdaContext


def describe_manage_cognito_domain():
    user_pool_id = "us-east-1_abcdefgh"
    domain_prefix = "mytestdomain"
    event = {
        "ResourceProperties": {
            "UserPoolId": user_pool_id,
            "DomainPrefix": domain_prefix
        },
        "ResponseURL": "bar",
        "StackId": "quz",
        "RequestId": "my-request-id",
        "LogicalResourceId": "my-logical-resource-id",
    }

    # Create a Cognito IDP client
    client = boto3.client('cognito-idp', region_name='us-east-1')

    @mock_aws
    def test_delete_domain_on_stack_delete(mocker):
        # ARRANGE
        # Create a user pool
        pool_response = client.create_user_pool(
            PoolName='MyTestUserPool'
        )
        # Retrieve the user pool ID from the response
        user_pool_id = pool_response['UserPool']['Id']

        # Define a domain for the user pool
        domain = 'mytestdomain'

        # Add the domain to the user pool
        client.create_user_pool_domain(
            Domain=domain,
            UserPoolId=user_pool_id
        )

        mock_cfnresponse = mocker.patch('cfnresponse.send')
        event['RequestType'] = 'Delete'
        event['ResourceProperties'] = {
            "UserPoolId": user_pool_id,
            "DomainPrefix": domain
        }

        # ACT
        lambda_handler(event, TestLambdaContext())

        # ASSERT
        mock_cfnresponse.assert_called_once()
        args, kwargs = mock_cfnresponse.call_args
        assert args[2] == 'SUCCESS'

    @mock_aws
    def test_failed_to_delete_domain(mocker):
        # ARRANGE
        mock_cfnresponse = mocker.patch('cfnresponse.send')
        event['RequestType'] = 'Delete'
        event['ResourceProperties'] = {
            "UserPoolId": user_pool_id,  # userpool doesn't exist
            "DomainPrefix": 'foo'
        }

        # ACT
        lambda_handler(event, TestLambdaContext())

        # ASSERT
        mock_cfnresponse.assert_called_once()
        args, kwargs = mock_cfnresponse.call_args
        assert args[2] == 'FAILED'

    @mock_aws
    def test_create_domain_on_stack_create(mocker):
        # ARRANGE
        # Create a user pool
        pool_response = client.create_user_pool(
            PoolName='MyTestUserPool'
        )
        # Retrieve the user pool ID from the response
        user_pool_id = pool_response['UserPool']['Id']

        # Define a domain for the user pool
        domain = 'mytestdomain'

        mock_cfnresponse = mocker.patch('cfnresponse.send')
        event['RequestType'] = 'Create'
        event['ResourceProperties'] = {
            "UserPoolId": user_pool_id,
            "DomainPrefix": domain
        }

        # ACT
        lambda_handler(event, TestLambdaContext())

        # ASSERT
        mock_cfnresponse.assert_called_once()
        args, kwargs = mock_cfnresponse.call_args
        assert args[2] == 'SUCCESS'

    @mock_aws
    def test_failed_to_create_domain(mocker):
        # ARRANGE
        mock_cfnresponse = mocker.patch('cfnresponse.send')
        event['RequestType'] = 'Create'
        event['ResourceProperties'] = {
            "UserPoolId": user_pool_id,  # userpool doesn't exist
            "DomainPrefix": 'foo'
        }

        # ACT
        lambda_handler(event, TestLambdaContext())

        # ASSERT
        mock_cfnresponse.assert_called_once()
        args, kwargs = mock_cfnresponse.call_args
        assert args[2] == 'FAILED'

    @mock_aws
    def test_update_domain_on_stack_update(mocker):
        # ARRANGE
        # Create a user pool
        pool_response = client.create_user_pool(
            PoolName='MyTestUserPool'
        )
        # Retrieve the user pool ID from the response
        user_pool_id = pool_response['UserPool']['Id']

        # Define a domain for the user pool
        domain = 'mytestdomain'

        # Add the domain to the user pool
        client.create_user_pool_domain(
            Domain=domain,
            UserPoolId=user_pool_id
        )

        mock_cfnresponse = mocker.patch('cfnresponse.send')
        event['RequestType'] = 'Update'
        event['ResourceProperties'] = {
            "UserPoolId": user_pool_id,
            "DomainPrefix": 'new-domain'
        }
        event['OldResourceProperties'] = {
            "DomainPrefix": domain
        }

        # ACT
        lambda_handler(event, TestLambdaContext())

        # ASSERT
        mock_cfnresponse.assert_called_once()
        args, kwargs = mock_cfnresponse.call_args
        assert args[2] == 'SUCCESS'
