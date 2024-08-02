#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
import os

import pytest
from aws_lambda_powertools import Logger
from moto import mock_s3, mock_sts

from assessment_runner.jobs_repository import JobsRepository

os.environ['AWS_REGION'] = 'us-east-1'
from resource_based_policy.step_functions_lambda.scan_s3_bucket_policy import S3BucketPolicy
from tests.test_resource_based_policy.mock_data import mock_policies, event

logger = Logger(level="info")


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
    number_of_buckets = 0
    for policy_object in mock_policies:
        if policy_object.get('MockResourceName'):
            bucket = s3_client_resource.Bucket(policy_object.get('MockResourceName'))
            bucket.create()
            number_of_buckets += 1
            if policy_object.get('MockPolicy'):  # skip if no policy
                s3_client.put_bucket_policy(
                    Bucket=policy_object.get('MockResourceName'),
                    Policy=json.dumps(policy_object.get('MockPolicy')))
                logger.info(f"For S3 Bucket: {policy_object.get('MockResourceName')} "
                            f"put policy: {policy_object.get('MockPolicy')}")
    yield number_of_buckets

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


@mock_sts
def test_s3_policy_scan_get_bucket_location_catches_error(job_history_table, s3_setup, mocker):
    mock_get_bucket_location = mocker.patch('aws.services.s3.S3.get_bucket_location')
    # Simulate the first and third call raising exceptions, every other call succeeding
    mock_get_bucket_location.side_effect = [Exception("Access Denied"), "us-east-1", Exception("Not Found")] + [
        "us-west-2"] * 100

    s3_bucket_policy = S3BucketPolicy(event)

    response = s3_bucket_policy.scan()
    logger.info(response)

    # Verify that get_bucket_location was called for each bucket, doesn't abort scan after the first error
    number_of_buckets = s3_setup
    assert mock_get_bucket_location.call_count == number_of_buckets

    failed_tasks = JobsRepository().find_task_failures_by_job_id(
        event['JobId']
    )

    # Verify that the failed tasks are stored in dynamodb, so the user knows which buckets they need to check manually
    assert len(failed_tasks) == 2
    expected_errors = {
        'Unable to get_bucket_location for bucket resource_1: Access Denied',
        'Unable to get_bucket_location for bucket resource_3: Not Found'
    }
    actual_errors = set(task['Error'] for task in failed_tasks)
    assert actual_errors == expected_errors
