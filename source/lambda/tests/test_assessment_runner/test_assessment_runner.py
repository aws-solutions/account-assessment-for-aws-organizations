# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import List, Dict

import pytest
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

from assessment_runner.assessment_runner import AssessmentRunner, SynchronousScanStrategy
from assessment_runner.job_model import JobModel
from assessment_runner.jobs_repository import JobsRepository
from tests.test_utils.testdata_factory import job_create_request
from utils.api_gateway_lambda_handler import ClientException

item1 = job_create_request()
item2 = job_create_request(job_status='FINISHED')
logger = Logger(level="info")


def describe_assessment_runner():
    class MockStrategy(SynchronousScanStrategy):
        # AssessmentRunner can process different types of ScanStrategy that are be passed to it as argument.
        # This MockStrategy can be passed to AssessmentRunner in order to unit test AssessmentRunner itself,
        # without passing a real ScanStrategy with business logic.
        def __init__(self, fail: bool = False):
            self.logger = Logger("INFO")
            self.fail = fail  # if 'fail' is true, MockStrategy will simulate an error

        def assessment_type(self) -> str:
            return "MOCK_STRATEGY"

        def scan(self, job_id: str, request_body) -> List[Dict]:
            if self.fail:
                raise IndexError('Some error')
            else:
                return []

        def write(self, items: List[Dict]):
            self.logger.info(items)

    def test_that_it_fails_when_there_is_an_active_job(job_history_table):
        # ARRANGE
        noop_strategy = MockStrategy()
        event = APIGatewayProxyEvent(data={"requestContext": {"authorizer": {"claims": {"email": "some-useremail"}}}})

        repository = JobsRepository()
        job = repository.create_job(item1)
        active_job: JobModel = dict(job, AssessmentType='MOCK_STRATEGY')
        repository.put_last_job_marker(active_job)

        # ASSERT
        with pytest.raises(ClientException):
            # ACT
            AssessmentRunner(scan_strategy=noop_strategy).run_assessment(event, LambdaContext())

    def test_that_job_status_is_updated_to_succeeded(job_history_table):
        # ARRANGE
        repository = JobsRepository()
        noop_strategy = MockStrategy()
        event = APIGatewayProxyEvent(data={"requestContext": {"authorizer": {"claims": {"email": "some-useremail"}}}})

        # ACT
        job_model = AssessmentRunner(scan_strategy=noop_strategy).run_assessment(event, LambdaContext())

        # ASSERT
        item_in_ddb = repository.get_job(job_model['AssessmentType'], job_model['JobId'])
        assert item_in_ddb['JobStatus'] == 'SUCCEEDED'
        assert item_in_ddb['StartedBy'] == 'some-useremail'

    def test_that_job_status_is_updated_to_failed(job_history_table):
        # ARRANGE
        noop_strategy = MockStrategy(fail=True)
        event = APIGatewayProxyEvent(data={"requestContext": {"authorizer": {"claims": {"email": "some-useremail"}}}})
        repository = JobsRepository()

        # ACT
        with pytest.raises(Exception):
            AssessmentRunner(scan_strategy=noop_strategy).run_assessment(event, LambdaContext())

        # ASSERT
        items_in_ddb = repository.find_jobs_by_assessment_type(noop_strategy.assessment_type())
        assert items_in_ddb[0]['JobStatus'] == 'FAILED'

        active_marker = JobsRepository().get_last_job_marker(noop_strategy.assessment_type())
        assert active_marker['JobStatus'] == 'FAILED'
