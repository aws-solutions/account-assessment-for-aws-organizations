#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json

from aws_lambda_powertools import Logger

from assessment_runner import api_router
from assessment_runner.jobs_repository import JobsRepository
from tests.test_utils.testdata_factory import TestLambdaContext
from tests.test_utils.testdata_factory import job_create_request

item1 = job_create_request()
item2 = job_create_request(job_status='FINISHED')
logger = Logger(level="info")


def describe_read_job_history():
    event = {"path": "/jobs", "httpMethod": "GET"}

    def test_that_it_returns_an_empty_list(job_history_table):
        # ARRANGE

        # ACT
        result = api_router.lambda_handler(event, TestLambdaContext())

        # ASSERT
        assert result['statusCode'] == 200
        body = json.loads(result.get('body'))
        assert body['Results'] == []

    def test_that_when_put_2_items_it_returns_all_items(freeze_clock, job_history_table):
        # ARRANGE
        repository = JobsRepository()
        job1 = repository.create_job(item1)
        job2 = repository.create_job(item2)

        # ACT
        result = api_router.lambda_handler(event, TestLambdaContext())

        # ASSERT
        assert result['statusCode'] == 200
        body = json.loads(result.get('body'))
        assert job1 in body['Results']
        assert job2 in body['Results']

    def test_that_it_returns_only_latest_jobs(job_history_table):
        # ARRANGE
        repository = JobsRepository()
        job1 = repository.create_job(item1)
        job2 = repository.create_job(item2)

        repository.put_last_job_marker(job1)

        query_event = {
            **event,
            'queryStringParameters': {'selection': 'latest'}
        }

        # ACT
        result = api_router.lambda_handler(query_event, TestLambdaContext())
        # ASSERT
        body = json.loads(result.get('body'))
        assert job1 in body['Results']
        assert job2 not in body['Results']
