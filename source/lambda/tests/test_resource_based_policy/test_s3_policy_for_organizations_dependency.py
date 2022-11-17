# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from aws_lambda_powertools import Logger
from resource_based_policy.step_functions_lambda.scan_policy_all_services import S3BucketPolicy
import pytest
from moto import mock_s3, mock_sts
from tests.test_resource_based_policy.mock_data import mock_policies, event

logger = Logger(loglevel="info")


@mock_sts
@mock_s3
def test_s3_policy_scan_no_buckets():
    # ACT
    response = S3BucketPolicy(event).scan()
    logger.info(response)

    # ASSERT
    # ASSERT
    assert response == []


@pytest.fixture
def s3_setup(s3_client, s3_client_resource):
    # ARRANGE
    for policy_object in mock_policies:
        if policy_object.get('MockResourceName'):
            bucket = s3_client_resource.Bucket(policy_object.get('MockResourceName'))
            bucket.create()
            if policy_object.get('MockPolicy'):  # skip if no policy
                s3_client.put_bucket_policy(
                    Bucket=policy_object.get('MockResourceName'),
                    Policy=json.dumps(policy_object.get('MockPolicy')))
                logger.info(f"For S3 Bucket: {policy_object.get('MockResourceName')} "
                            f"put policy: {policy_object.get('MockPolicy')}")


@mock_sts
def test_s3_policy_scan(s3_setup):

    # ACT
    response = S3BucketPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 6
    for resource in response:
        assert resource['DependencyType'] in [
            'aws:PrincipalOrgID',
            'aws:PrincipalOrgPaths',
            'aws:ResourceOrgID',
            'aws:ResourceOrgPaths'
        ]

