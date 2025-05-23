#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

import boto3
from aws_lambda_powertools import Logger
from moto import mock_aws

from policy_explorer.step_functions_lambda.scan_sns_topic_policy import SNSTopicPolicy
from tests.test_policy_explorer.mock_data import mock_policies, event
from policy_explorer.policy_explorer_model import PolicyType



logger = Logger(level="info")


@mock_aws
def test_sns_policy_scan_no_topics():
    # ACT
    response = SNSTopicPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_aws
def test_sns_policy_scan():
    # ARRANGE
    for region in event['Regions']:
        sns_client = boto3.client("sns", region_name=region)
        for policy_object in mock_policies:
            if policy_object.get('MockResourceName'):
                attributes = {"DisplayName": f"{policy_object.get('MockResourceName')}_{region}"}
                # if no policy is present the topic is created with default policy
                if policy_object.get('MockPolicy'):
                    attributes.update({"Policy": json.dumps(policy_object.get('MockPolicy'))})
                response = sns_client.create_topic(
                    Name=f"{policy_object.get('MockResourceName')}_{region}",
                    Attributes=attributes
                )
                logger.info(f"Topic ARN created: {response.get('TopicArn')}"
                            f" with policy: {policy_object.get('MockPolicy')}")

    # ACT
    response = SNSTopicPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 28
    for resource in response:
        assert resource.get('PartitionKey') == PolicyType.RESOURCE_BASED_POLICY.value