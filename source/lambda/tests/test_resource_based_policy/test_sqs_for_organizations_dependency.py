# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json

import boto3
from aws_lambda_powertools import Logger
from moto import mock_sts, mock_sqs
from mypy_boto3_sqs.literals import QueueAttributeNameType

from resource_based_policy.step_functions_lambda.scan_sqs_queue_policies import SQSQueuePolicy
from tests.test_resource_based_policy.mock_data import event, mock_policies

logger = Logger(level="info")


@mock_sts
@mock_sqs
def test_no_sqs():
    # ACT
    response = SQSQueuePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0


@mock_sts
@mock_sqs
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
    assert len(list(response)) == 12
    for resource in response:
        assert resource['DependencyType'] in [
            'aws:PrincipalOrgID',
            'aws:PrincipalOrgPaths',
            'aws:ResourceOrgID',
            'aws:ResourceOrgPaths'
        ]
