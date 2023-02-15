# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json

import boto3
from aws_lambda_powertools import Logger
from moto import mock_sts, mock_mediastore

from resource_based_policy.step_functions_lambda.scan_media_store_policy import MediaStorePolicy
from tests.test_resource_based_policy.mock_data import event, mock_policies

logger = Logger(level="info")


@mock_sts
@mock_mediastore
def test_no_mediastore_keys():
    # ACT
    response = MediaStorePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0


@mock_sts
@mock_mediastore
def test_mediastore_key_no_policy():
    # ARRANGE
    for region in event['Regions']:
        media_store_client = boto3.client("mediastore", region_name=region)
        for policy_object in mock_policies:
            if policy_object.get('MockResourceName'):
                media_store_client.create_container(
                    ContainerName=policy_object.get('MockResourceName'),
                    Tags=[{"Key": "customer"}]
                )
                if policy_object.get('MockPolicy'):
                    media_store_client.put_container_policy(
                        ContainerName=policy_object.get('MockResourceName'),
                        Policy=json.dumps(policy_object.get('MockPolicy'))
                    )

    response = MediaStorePolicy(event).scan()
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
