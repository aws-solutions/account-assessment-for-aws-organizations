# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from aws_lambda_powertools import Logger
from resource_based_policy.step_functions_lambda.scan_policy_all_services import GlacierVaultPolicy
import pytest
from moto import mock_glacier, mock_sts
from tests.test_resource_based_policy.mock_data import mock_policies, event

logger = Logger(loglevel="info")


@mock_sts
@mock_glacier
def test_glacier_vault_policy_scan_no_vaults():
    # ACT
    response = GlacierVaultPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []

