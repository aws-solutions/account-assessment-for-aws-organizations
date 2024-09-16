#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import uuid

from aws_lambda_powertools import Logger
from moto import mock_aws

from delegated_admins.scan_for_delegated_admins import \
    DelegatedAdminsStrategy

logger = Logger(level="info")


@mock_aws
def test_delegated_admin_account_scan(org_client, organizations_setup):
    # ARRANGE
    dev_account_id = organizations_setup['dev_account_id']
    dev_account_id_2 = organizations_setup['dev_account_id_2']
    job_id = str(uuid.uuid4())

    org_client.register_delegated_administrator(
        AccountId=dev_account_id,
        ServicePrincipal="ssm.amazonaws.com"
    )

    org_client.register_delegated_administrator(
        AccountId=dev_account_id,
        ServicePrincipal="guardduty.amazonaws.com"
    )

    org_client.register_delegated_administrator(
        AccountId=dev_account_id_2,
        ServicePrincipal="guardduty.amazonaws.com"
    )

    # ACT
    delegated_admin_accounts = DelegatedAdminsStrategy().scan(job_id, {})
    logger.info(f"Delegated Admin Accounts and Services: {delegated_admin_accounts}")

    # ASSERT
    assert len(delegated_admin_accounts) == 3
    for account in delegated_admin_accounts:
        assert "Id" not in account.keys()
        assert "AccountId" in account.keys()
        assert "ServicePrincipal" in account.keys()
        assert "Arn" in account.keys()
        assert "Email" in account.keys()
        assert "Name" in account.keys()
        assert "Status" in account.keys()
        assert "JoinedMethod" in account.keys()
        assert "JoinedTimestamp" in account.keys()
        assert "DelegationEnabledDate" in account.keys()
        assert "JobId" in account.keys()
        assert "AssessedAt" in account.keys()
        assert type(account.get("AssessedAt")) == str
