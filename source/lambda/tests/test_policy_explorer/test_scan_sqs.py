#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

import boto3
from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_sqs.literals import QueueAttributeNameType

from policy_explorer.step_functions_lambda.scan_sqs_queue_policies import SQSQueuePolicy
from tests.test_policy_explorer.mock_data import event, mock_policies
from policy_explorer.policy_explorer_model import PolicyType

logger = Logger(level="info")


@mock_aws
def test_no_sqs():
    # ACT
    response = SQSQueuePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0


@mock_aws
def test_sqs_policy_scan():
    # ARRANGE
    for region in event['Regions']:
        sqs_client = boto3.client("sqs", region_name=region)
        for policy_object in mock_policies:
            if policy_object.get('MockResourceName'):
                attributes: dict[QueueAttributeNameType, str] = {
                    "DelaySeconds": "900",
                    "MaximumMessageSize": "262144",
                    "MessageRetentionPeriod": "1209600",
                    "ReceiveMessageWaitTimeSeconds": "20",
                    "VisibilityTimeout": "43200",
                }
                # if no policy is present the topic is created with default policy
                if policy_object.get('MockPolicy'):
                    attributes.update({'Policy': json.dumps(policy_object.get('MockPolicy'))})
                sqs_client.create_queue(
                    QueueName=policy_object.get('MockResourceName'),
                    Attributes=attributes)

    # ACT
    response = SQSQueuePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 26
    for resource in response:
        assert resource.get('PartitionKey') == PolicyType.RESOURCE_BASED_POLICY.value
