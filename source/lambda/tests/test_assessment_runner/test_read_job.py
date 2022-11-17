# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import uuid

from aws_lambda_powertools.utilities.typing import LambdaContext

from assessment_runner import api_router
from assessment_runner.job_model import JobDetails
from assessment_runner.jobs_repository import JobsRepository
from tests.test_utils.testdata_factory import job_create_request

item1 = job_create_request(assessment_type='DELEGATED_ADMIN')
item2 = job_create_request(assessment_type='DELEGATED_ADMIN', job_status='FINISHED')


def describe_read_job():
    def test_that_it_returns_400_job_not_found(job_history_table):
        # ARRANGE
        event = {"path": "/jobs/DELEGATED_ADMIN/" + uuid.uuid4().hex, "httpMethod": "GET"}

        # ACT
        result = api_router.lambda_handler(event, LambdaContext())

        # ASSERT
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert body['Error'] == "Job not found"

    def test_that_it_returns_job_with_given_key(job_history_table, delegated_admin_table):
        # ARRANGE
        job = JobsRepository().create_job(item1)
        JobsRepository().create_job(item2)

        event = {"path": f"/jobs/{job['AssessmentType']}/{job['JobId']}", "httpMethod": "GET"}

        # ACT
        result = api_router.lambda_handler(event, LambdaContext())

        # ASSERT
        assert result['statusCode'] == 200
        body: JobDetails = json.loads(result['body'])
        assert body['Job']['JobId'] == job['JobId']
