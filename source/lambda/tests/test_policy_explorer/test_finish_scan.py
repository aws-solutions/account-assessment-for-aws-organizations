# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from datetime import datetime

from aws_lambda_powertools import Logger

from assessment_runner.job_model import JobModel, JobCreateRequest, JobTaskFailureCreateRequest
from assessment_runner.jobs_repository import JobsRepository
from policy_explorer.finish_scan import FinishScanForResourceBasedPolicies
from tests.test_utils.testdata_factory import job_create_request

request1: JobCreateRequest = job_create_request()
request2 = job_create_request()
logger = Logger(level="info")


def describe_finish_scan():
    def test_that_it_returns_succeeded(job_history_table, resource_based_policies_table):
        # ARRANGE
        repository = JobsRepository()
        job = repository.create_job(request1)
        repository.create_job(request2)

        active_job: JobModel = dict(job, AssessmentType=request1['AssessmentType'])
        repository.put_last_job_marker(active_job)

        # ACT
        response = FinishScanForResourceBasedPolicies().finish(job['AssessmentType'], job['JobId'])

        # ASSERT
        assert response["Status"] == 'SUCCEEDED'

    def test_that_it_returns_succeeded_with_failures(job_history_table, resource_based_policies_table):
        # ARRANGE
        repository = JobsRepository()
        job = repository.create_job(request1)
        repository.create_job(request2)

        active_job: JobModel = dict(job, AssessmentType=request1['AssessmentType'])
        repository.put_last_job_marker(active_job)

        task_failure: JobTaskFailureCreateRequest = {
            'JobId': job['JobId'],
            'AssessmentType': job['AssessmentType'],
            'ServiceName': 'S3',
            'AccountId': '111122223333',
            'Region': 'us-east-1',
            'FailedAt': datetime.now().isoformat(),
            'Error': 'Unknown error'
        }
        repository.create_job_task_failure(task_failure)

        # ACT
        response = FinishScanForResourceBasedPolicies().finish(job['AssessmentType'], job['JobId'])

        # ASSERT
        assert response["Status"] == 'SUCCEEDED_WITH_FAILED_TASKS'
