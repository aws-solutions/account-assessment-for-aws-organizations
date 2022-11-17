# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from aws_lambda_powertools import Logger
from resource_based_policy.step_functions_lambda.scan_policy_all_services_router import lambda_handler
from moto import mock_sts, mock_dynamodb, mock_s3
from tests.test_resource_based_policy.mock_data import event

logger = Logger(loglevel="info")
event['ServiceName'] = 's3'
context = {}


@mock_s3
@mock_dynamodb
@mock_sts
def test_lambda_function():
    # ACT
    response = lambda_handler(event, context)
    logger.info(response)

    # ASSERT
    assert response is None

