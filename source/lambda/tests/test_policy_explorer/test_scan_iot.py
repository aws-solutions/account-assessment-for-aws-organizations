#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

import boto3
from aws_lambda_powertools import Logger
from moto import mock_aws

from policy_explorer.policy_explorer_model import PolicyType
from policy_explorer.step_functions_lambda.scan_iot_policy import IoTPolicy
from tests.test_policy_explorer.mock_data import event, mock_policies

logger = Logger(level="info")


@mock_aws
def test_no_iot_policy():
    # ACT
    response = IoTPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0


@mock_aws
def test_iot_policy_scan():
    # ARRANGE
    for region in event['Regions']:
        iot_client = boto3.client("iot", region_name=region)
        for policy_object in mock_policies:
            if policy_object.get('MockResourceName'):
                if policy_object.get('MockPolicy'):
                    iot_client.create_policy(
                        policyName=policy_object.get('MockResourceName'),
                        policyDocument=json.dumps(policy_object.get('MockPolicy')))

    # ACT
    response = IoTPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 26
    for resource in response:
        assert resource.get('PartitionKey') == PolicyType.RESOURCE_BASED_POLICY.value
        assert resource.get('Region') in ['us-east-1', 'eu-west-1']
