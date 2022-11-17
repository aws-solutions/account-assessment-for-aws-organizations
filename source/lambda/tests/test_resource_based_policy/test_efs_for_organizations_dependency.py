# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json

import boto3
from aws_lambda_powertools import Logger

from resource_based_policy.step_functions_lambda.scan_policy_all_services import ElasticFileSystemPolicy
from moto import mock_sts, mock_efs
from tests.test_resource_based_policy.mock_data import event

logger = Logger(loglevel="info")


@mock_sts
@mock_efs
def test_no_efs():
    # ACT
    response = ElasticFileSystemPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0

