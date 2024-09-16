#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

import boto3
from aws_lambda_powertools import Logger
from moto import mock_aws

from resource_based_policy.step_functions_lambda.scan_api_gateway_service_policy import APIGatewayPolicy
from tests.test_resource_based_policy.mock_data import event, mock_policies

logger = Logger(level="info")


@mock_aws
def test_no_apigateway():
    # ACT
    response = APIGatewayPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0


@mock_aws
def test_api_gateway_no_policy():
    # ARRANGE
    for region in event['Regions']:
        apigateway_client = boto3.client("apigateway", region_name=region)
        create_response = apigateway_client.create_rest_api(name="my_api", description="this is my api")
        logger.info(create_response)

    # ACT
    response = APIGatewayPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0


@mock_aws
def test_apigateway_with_policy():
    # ARRANGE
    for region in event['Regions']:
        apigateway_client = boto3.client("apigateway", region_name=region)
        for policy_object in mock_policies:
            if policy_object.get('MockResourceName'):
                # if no policy is present the topic is created with default policy
                if policy_object.get('MockPolicy'):
                    apigateway_client.create_rest_api(
                        name=policy_object.get('MockResourceName'),
                        description=f"TestApiDescription-{policy_object.get('MockResourceName')}",
                        policy=json.dumps(policy_object.get('MockPolicy')))

    # ACT
    response = APIGatewayPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 16
    for resource in response:
        assert resource['DependencyType'] in [
            'aws:PrincipalOrgID',
            'aws:PrincipalOrgPaths',
            'aws:ResourceOrgID',
            'aws:ResourceOrgPaths',
            'aws:SourceOrgID',
            'aws:SourceOrgPaths'
        ]
