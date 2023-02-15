# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json

import boto3
from aws_lambda_powertools import Logger
from moto import mock_ecr, mock_sts

from resource_based_policy.step_functions_lambda.scan_ec2_container_registry_repository_policy import \
    EC2ContainerRegistryRepositoryPolicy
from tests.test_resource_based_policy.mock_data import mock_policies, event

logger = Logger(level="info")


@mock_sts
@mock_ecr
def test_ecr_policy_scan_no_topics():
    # ACT
    response = EC2ContainerRegistryRepositoryPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_sts
@mock_ecr
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
    assert len(list(response)) == 12
    for resource in response:
        assert resource['DependencyType'] in [
            'aws:PrincipalOrgID',
            'aws:PrincipalOrgPaths',
            'aws:ResourceOrgID',
            'aws:ResourceOrgPaths'
        ]

