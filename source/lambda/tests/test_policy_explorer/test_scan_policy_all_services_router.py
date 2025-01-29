#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from unittest.mock import patch

from aws_lambda_powertools import Logger
from moto import mock_aws

from policy_explorer.step_functions_lambda.scan_policy_all_services_router import lambda_handler
from tests.test_policy_explorer.mock_data import event
from tests.test_utils.testdata_factory import TestLambdaContext

logger = Logger(level="info")
event['ServiceName'] = 's3'


@mock_aws
def test_lambda_function():
    # ACT
    response = lambda_handler(event, TestLambdaContext())
    logger.info(response)

    # ASSERT
    assert response is None


def mock_write_task_failure(job_id: str, policy_type_key:str, account_id: str, region: str, service_name: str, message: str):
    assert job_id == "12345-45678-098765"
    assert policy_type_key == "POLICY_EXPLORER"
    assert account_id == "123456789012"
    assert region is None
    assert service_name == "no-service"
    assert message == 'Unsupported Service'


@mock_aws
@patch('policy_explorer.step_functions_lambda.scan_policy_all_services_router.write_task_failure', mock_write_task_failure)
def test_service_with_no_scan_policy(): 
    
    event['ServiceName'] = 'no-service'
    #ACT
    response = lambda_handler(event, TestLambdaContext())
    logger.info(type(response))
    
    assert response is None