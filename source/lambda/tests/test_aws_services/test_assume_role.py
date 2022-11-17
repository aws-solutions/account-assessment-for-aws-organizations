# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from moto import mock_sts

from aws.services.security_token_service import SecurityTokenService

logger = Logger(loglevel="info")


@mock_sts
def test_assume_role_in_same_account(organizations_setup):
    # ARRANGE
    sts = SecurityTokenService()
    current_account_id = sts.get_caller_identity().get('Account')

    # ACT
    credentials = sts.assume_role_by_name(current_account_id, 'SomeRole')

    # ASSERT
    assert "AccessKeyId" in credentials.keys()
    assert "SecretAccessKey" in credentials.keys()
    assert "SessionToken" in credentials.keys()
    assert "Expiration" in credentials.keys()


@mock_sts
def test_assume_role_in_different_account(org_client, organizations_setup):
    # ARRANGE
    sts = SecurityTokenService()
    member_account_id = get_member_account_id(org_client)

    # ACT
    credentials = sts.assume_role_by_name(member_account_id, 'SomeRole')

    # ASSERT
    assert "AccessKeyId" in credentials.keys()
    assert "SecretAccessKey" in credentials.keys()
    assert "SessionToken" in credentials.keys()
    assert "Expiration" in credentials.keys()


def get_member_account_id(org_client):
    accounts_response = org_client.list_accounts().get("Accounts")
    for account in accounts_response:
        if account.get("Name") != "master":
            return account.get("Id")
