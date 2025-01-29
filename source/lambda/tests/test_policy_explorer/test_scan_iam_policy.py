#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

import pytest
from aws_lambda_powertools import Logger
from moto import mock_aws

from policy_explorer.policy_explorer_model import PolicyType
from policy_explorer.step_functions_lambda.scan_iam_policy import IAMPolicy
from tests.test_policy_explorer.mock_data import mock_policies, event

logger = Logger(level="info")


@mock_aws
def test_scan_no_roles_no_policies():
    # ARRANGE

    # ACT
    response = IAMPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@pytest.fixture
def iam_setup(iam_client):
    # ARRANGE
    # Create multiple IAM Polies and IAM Roles (with and without attached policies)
    assumed_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "",
                "Effect": "Allow",
                "Principal": {
                    "AWS": "*"
                },
                "Action": "sts:AssumeRole",
                "Condition": {"StringEquals": {"aws:PrincipalOrgID": "o-a1b2c3d4e5"}}
            }
        ]
    }

    for policy_object in mock_policies:
        if policy_object.get('MockPolicy'):
            iam_client.create_policy(
                PolicyName=policy_object.get('MockPolicyName'),
                PolicyDocument=json.dumps(policy_object.get('MockPolicy')))

        if policy_object.get('MockResourceName'):
            iam_client.create_role(
                RoleName=policy_object.get('MockResourceName'),
                AssumeRolePolicyDocument=json.dumps(assumed_role_policy),
                Path="/my-path/")
            if policy_object.get('MockPolicy'):
                iam_client.put_role_policy(
                    RoleName=policy_object.get('MockResourceName'),
                    PolicyName="test policy",
                    PolicyDocument=json.dumps(policy_object.get('MockPolicy')))


@mock_aws
def test_scan_iam_policies(iam_setup):
    # ACT
    response = IAMPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 41
    for resource in response:
        if resource.get('ResourceIdentifier').__contains__("AssumeRolePolicyDocument"):
            assert resource.get('PartitionKey') == PolicyType.RESOURCE_BASED_POLICY.value
        else:
            assert resource.get('PartitionKey') == PolicyType.IDENTITY_BASED_POLICY.value
            
