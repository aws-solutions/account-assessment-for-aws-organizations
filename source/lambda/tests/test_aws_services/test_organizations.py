#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from moto import mock_aws

from aws.services.organizations import Organizations

logger = Logger(level="info")


@mock_aws
def test_get_active_accounts(organizations_setup):
    # ARRANGE
    all_accounts = Organizations().list_accounts()

    # ACT
    accounts = Organizations().list_active_account_ids()

    # ASSERT
    assert len(all_accounts) == len(accounts)


@mock_aws
def test_exclude_suspended_accounts(org_client, organizations_setup):
    # ARRANGE
    all_accounts = Organizations().list_accounts()
    suspend_account = _get_member_account_id(all_accounts)
    org_client.close_account(AccountId=suspend_account)

    # ACT
    active_accounts = Organizations().list_active_account_ids()

    # ASSERT
    assert len(all_accounts) - 1 == len(active_accounts)


def _get_member_account_id(all_accounts):
    logger.info(f"List accounts BEFORE closing account: {all_accounts}")
    for account in all_accounts:
        if account.get("Name") != "master":  # skip closing management account
            if account.get("Status") == "ACTIVE":
                return account.get("Id")


@mock_aws
def test_list_policies_idempotent(organizations_setup):
    # ARRANGE
    all_policies = Organizations().list_policies()

    # ACT
    policies = Organizations().list_policies()

    # ASSERT
    assert len(all_policies) == len(policies)
    assert all(policy["Type"] == "SERVICE_CONTROL_POLICY" for policy in policies)
    assert policies


@mock_aws
def test_describe_policy(organizations_setup):
    # ARRANGE
    policy_id = Organizations().list_policies()[0].get("Id")
    policy_content = Organizations().describe_policy(policy_id)
    # ACT
    policy = Organizations().describe_policy(policy_id)
    # ASSERT
    assert policy_content == policy
