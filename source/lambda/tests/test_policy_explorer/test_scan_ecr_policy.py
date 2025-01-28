#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

import boto3
from aws_lambda_powertools import Logger
from moto import mock_aws

from policy_explorer.policy_explorer_model import PolicyType
from policy_explorer.step_functions_lambda.scan_ec2_container_registry_repository_policy import \
    EC2ContainerRegistryRepositoryPolicy
from tests.test_policy_explorer.mock_data import mock_policies, event

logger = Logger(level="info")


@mock_aws
def test_ecr_policy_scan_no_topics():
    # ACT
    response = EC2ContainerRegistryRepositoryPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_aws
def test_ecr_policy_scan():
    # ARRANGE
    for region in event['Regions']:
        ecr_client = boto3.client("ecr", region_name=region)
        for policy_object in mock_policies:
            if policy_object.get('MockResourceName'):
                ecr_client.create_repository(
                    repositoryName=policy_object.get('MockResourceName')
                )
                if policy_object.get('MockPolicy'):
                    ecr_client.set_repository_policy(
                        repositoryName=policy_object.get('MockResourceName'),
                        policyText=json.dumps(policy_object.get('MockPolicy'))
                    )

    # ACT
    response = EC2ContainerRegistryRepositoryPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 26
    for resource in response:
        assert resource.get('PartitionKey') == PolicyType.RESOURCE_BASED_POLICY.value