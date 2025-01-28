# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
from os import getenv

import pytest
from aws_lambda_powertools import Logger
from moto.core import DEFAULT_ACCOUNT_ID as ACCOUNT_ID

from assessment_runner.job_model import JobTaskFailureCreateRequest
from assessment_runner.jobs_repository import JobsRepository
from aws.utils.exceptions import RegionNotEnabled, ServiceUnavailable, ConnectionTimeout
from aws.utils.exceptions import service_exception_handler
from policy_explorer.policy_explorer_model import ScanServiceRequestModel
from policy_explorer.step_functions_lambda.utils import scan_regions
from tests.test_policy_explorer.mock_data import event as event_from_api_gateway

REGION = 'us-east-1'
logger = Logger(service='test_exception_handler', level='INFO')


# ARRANGE
class MockService:
    def __init__(self, account_id, region):
        self.account_id = account_id
        self.region = region

    @service_exception_handler
    def list_regions(self):
        logger.info(f"Printing region: {self.region}")
        return [self.region]

    @service_exception_handler
    def raise_region_not_enabled(self):
        raise RegionNotEnabled(self.region)

    @service_exception_handler
    def raise_service_unavailable(self):
        raise ServiceUnavailable(self.region)

    @service_exception_handler
    def raise_connection_timeout(self):
        raise ConnectionTimeout(self.region)


# ARRANGE
class ScanTestService:
    def __init__(self, event: ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self):
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region_name: str):
        test_resources_in_all_regions = []
        self.logger.info(f"Scanning Test Policies in {region_name}")
        test_client = MockService(self.account_id, region_name)
        objects = test_client.list_regions()
        test_resources_in_all_regions.extend(objects)
        return test_resources_in_all_regions

    def raise_region_not_enabled(self):
        return scan_regions(self.event, self.raise_single_region_not_enabled)

    def raise_single_region_not_enabled(self, region_name):
        test_resources_in_all_regions = []
        self.logger.info(f"Scanning Test Policies in {region_name}")
        test_client = MockService(self.account_id, region_name)
        if region_name == REGION:
            test_client.raise_region_not_enabled()
        objects = test_client.list_regions()
        test_resources_in_all_regions.extend(objects)
        self.logger.info(f"RETURNING: {test_resources_in_all_regions}")
        return test_resources_in_all_regions


def test_list_regions():
    # ACT
    list_of_regions = MockService(ACCOUNT_ID, REGION).list_regions()

    # ASSERT
    assert list_of_regions == [REGION]


def test_raise_region_not_enabled():
    # ACT
    with pytest.raises(Exception) as exc_info:
        MockService(ACCOUNT_ID, REGION).raise_region_not_enabled()

    # ASSERT
    assert exc_info.value.args[0] == f"{REGION} is disabled, you must enable it before scanning resources in this " \
                                     f"region."


def test_raise_service_unavailable():
    # ACT
    with pytest.raises(Exception) as exc_info:
        MockService(ACCOUNT_ID, REGION).raise_service_unavailable()

    # ASSERT
    assert exc_info.value.args[0] == f"Service is not available in {REGION}."


def test_raise_connection_timeout():
    # ACT
    with pytest.raises(Exception) as exc_info:
        MockService(ACCOUNT_ID, REGION).raise_connection_timeout()

    # ASSERT
    assert exc_info.value.args[0] == f"Service endpoint connection timed out in {REGION}"


def test_scan_test_service():
    # ACT
    list_of_regions = ScanTestService(event_from_api_gateway).scan()

    # ASSERT
    assert list_of_regions == event_from_api_gateway['Regions']


def test_scan_region_not_enabled(job_history_table):
    # ACT
    list_of_regions = ScanTestService(event_from_api_gateway).raise_region_not_enabled()

    # ASSERT
    # remove REGION where exception was raised
    event_from_api_gateway['Regions'].remove(REGION)
    assert list_of_regions == event_from_api_gateway['Regions']

    failed_tasks = JobsRepository().find_task_failures_by_job_id(
        event_from_api_gateway['JobId']
    )

    assert len(failed_tasks) == 1
    item: JobTaskFailureCreateRequest
    for item in failed_tasks:
        assert item['Region'] == REGION
        assert item['Error'] == json.dumps(f"{REGION} is disabled, you must enable it before scanning resources in "
                                           f"this region.")
