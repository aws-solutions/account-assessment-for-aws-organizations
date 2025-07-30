#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

import pytest
from aws_lambda_powertools import Logger
from moto import mock_aws

from policy_explorer.policy_explorer_model import PolicyType
from policy_explorer.scan_single_service import ScanSingleServiceStrategy
from policy_explorer.step_functions_lambda.scan_s3_bucket_policy import S3BucketPolicy
from tests.test_policy_explorer.mock_data import mock_policies, event
from utils.api_gateway_lambda_handler import ClientException

logger = Logger(level="info")


@mock_aws
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


@mock_aws
def test_s3_policy_scan(mocker, s3_setup, job_history_table):
    def return_region(self, bucket_name):
        return "us-east-1"

    mocker.patch(
        "aws.services.s3.S3.get_bucket_location",
        return_region
    )

    # ACT
    response = ScanSingleServiceStrategy().scan('123', {
        'AccountId': '123456789012',
        'ServiceName': 's3',
        'Regions': ['us-east-1']
    })

    # ASSERT
    assert len(list(response)) == 13

    logger.info(response[0])
    assert response[0]['Action'] == '"s3:PutObject"'
    assert response[0]['SortKey'] == 'us-east-1#s3#123456789012#resource_1#1'
    assert response[0]['ResourceIdentifier'] == 'resource_1'
    assert response[0]['PartitionKey'] == PolicyType.RESOURCE_BASED_POLICY.value


@mock_aws
def test_invalid_region(mocker, s3_setup, job_history_table):
    # ARRANGE
    invalid_request = {
        'AccountId': '123456789012',
        'ServiceName': 's3',
        'Regions': ['invalid-region']
    }

    # ACT & ASSERT
    with pytest.raises(ClientException, match='No valid region'):
        ScanSingleServiceStrategy().scan('123', invalid_request)


@mock_aws
def test_invalid_service(mocker, s3_setup, job_history_table):
    # ARRANGE
    invalid_request = {
        'AccountId': '123456789012',
        'ServiceName': 'invalid-service',
        'Regions': ['us-east-1']
    }

    # ACT & ASSERT
    with pytest.raises(ClientException, match='Invalid service name'):
        ScanSingleServiceStrategy().scan('123', invalid_request)


@mock_aws
def test_invalid_account_id(mocker, s3_setup, job_history_table):
    # ARRANGE
    invalid_request = {
        'AccountId': 'invalid-account',
        'ServiceName': 's3',
        'Regions': ['us-east-1']
    }

    # ACT & ASSERT
    with pytest.raises(ClientException, match='Invalid AWS Account ID found'):
        ScanSingleServiceStrategy().scan('123', invalid_request)


@mock_aws
def test_s3_bucket_with_no_policy(mocker, s3_client_resource):
    # ARRANGE
    bucket_name = "bucket-without-policy"
    bucket = s3_client_resource.Bucket(bucket_name)
    bucket.create()
    
    def return_region(self, bucket_name):
        return "us-east-1"
    
    mocker.patch(
        "aws.services.s3.S3.get_bucket_location",
        return_region
    )
    
    # Mock get_bucket_policy to raise NoSuchBucketPolicy exception
    mock_s3_client = mocker.MagicMock()
    mock_s3_client.exceptions.NoSuchBucketPolicy = Exception
    mock_s3_client.get_bucket_policy.side_effect = mock_s3_client.exceptions.NoSuchBucketPolicy()
    
    # Mock _get_s3_client_with_regional_endpoint_if_opt_in_region to return our mock client
    mocker.patch.object(
        S3BucketPolicy,
        "_get_s3_client_with_regional_endpoint_if_opt_in_region",
        return_value=mock_s3_client
    )
    
    # Mock write_task_failure to verify it's not called
    write_task_failure_mock = mocker.patch("assessment_runner.assessment_runner.write_task_failure")

    # ACT
    response = S3BucketPolicy({
        'AccountId': '123456789012',
        'JobId': '123',
        'ServiceName': 's3',
        'Regions': ['us-east-1']
    }).scan()
    
    # ASSERT
    assert len(response) == 0  # No policies should be returned
    write_task_failure_mock.assert_not_called()  # Verify write_task_failure was not called
