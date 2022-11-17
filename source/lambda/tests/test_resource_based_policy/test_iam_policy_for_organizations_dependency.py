# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json

from aws_lambda_powertools import Logger
from resource_based_policy.step_functions_lambda.scan_policy_all_services import IAMPolicy
import pytest
from moto import mock_iam, mock_sts
from tests.test_resource_based_policy.mock_data import mock_policies, event

logger = Logger(loglevel="info")


@mock_sts
@mock_iam
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


@mock_sts
def test_scan_iam_policies(iam_setup):
    # ACT
    response = IAMPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 15
    for resource in response:
        assert resource['DependencyType'] in [
            'aws:PrincipalOrgID',
            'aws:PrincipalOrgPaths',
            'aws:ResourceOrgID',
            'aws:ResourceOrgPaths'
        ]
