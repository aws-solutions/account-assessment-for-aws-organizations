# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import uuid

from aws_lambda_powertools import Logger
from moto import mock_sts
from moto.core import DEFAULT_ACCOUNT_ID as ACCOUNT_ID

from aws.services.organizations import Organizations
from resource_based_policy.step_functions_lambda.validate_account_access import \
    ValidateAccountAccess, ValidationType

logger = Logger(level="info")


@mock_sts
def test_valid_account(organizations_setup):
    # ARRANGE
    job_id = str(uuid.uuid4())
    all_accounts = Organizations().list_accounts()
    logger.info(all_accounts)
    event = {
        "AccountId": '999999999999',
        "Regions": ['us-east-1', 'us-east-2'],
        "ServiceNames": ['s3', 'config'],
        "JobId": job_id
    }

    # ACT
    print(ACCOUNT_ID)
    status = ValidateAccountAccess(event).check_account_access_permission()
    logger.info(status)

    # ASSERT
    assert status.get('Validation') == str(ValidationType.SUCCEEDED.value)


@mock_sts
def test_invalid_account(organizations_setup, job_history_table):
    # ARRANGE
    job_id = str(uuid.uuid4())
    all_accounts = Organizations().list_accounts()
    for account in all_accounts:
        logger.info(f"Account Id: {account.get('Id')}")
    event = {
        "AccountId": '',
        "Regions": ['us-east-1', 'us-east-2'],
        "ServiceNames": ['s3', 'config'],
        "JobId": job_id
    }

    # ACT
    status = ValidateAccountAccess(event).check_account_access_permission()
    logger.info(status)

    # ASSERT
    assert status.get('Validation') == str(ValidationType.FAILED.value)
