# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import datetime

from aws_lambda_powertools import Logger
from moto import mock_sts
from mypy_boto3_backup.type_defs import BackupVaultListMemberTypeDef, GetBackupVaultAccessPolicyOutputTypeDef
from tests.test_resource_based_policy.mock_data import event
from resource_based_policy.step_functions_lambda.scan_backup_vault_access_policy import BackupVaultAccessPolicy

logger = Logger(level='info', service="test_code_build")


@mock_sts
def test_mock_backup_scan_policy_no_policies(mocker):
    # ARRANGE
    mock_backup(mocker)

    # ARRANGE
    response = BackupVaultAccessPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_sts
def test_mock_backup_scan_policy(mocker):
    # ARRANGE
    list_backup_vaults_response: list[BackupVaultListMemberTypeDef] = [
        {
            "BackupVaultName": "mock_name",
            "BackupVaultArn": "arn:mock_name",
            "CreationDate": datetime.datetime.now(),
            "EncryptionKeyArn": "arn:encryption_key_name",
            "CreatorRequestId": "id",
            "NumberOfRecoveryPoints": 1,
            "Locked": False,
            "MinRetentionDays": 1,
            "MaxRetentionDays": 2,
            "LockDate": datetime.datetime.now()
        }
    ]

    get_backup_vault_access_policy_response: GetBackupVaultAccessPolicyOutputTypeDef = {
        "BackupVaultName": "mock_name",
        "BackupVaultArn": "arn:mock_name",
        "Policy": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":["
                  "\"backup:SendEmail\",\"backup:SendRawEmail\"],\"Resource\":\"*\",\"Condition\":{"
                  "\"StringEquals\":{\"aws:PrincipalOrgID\":\"o-a1b2c3d4e5\"}}}]}",
        "ResponseMetadata": {
            "RequestId": "request_id",
            "HostId": "host_id",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {"mock_key": "mock_value"},
            "RetryAttempts": 3,
        }
    }

    mock_backup(mocker,
                list_backup_vaults_response,
                get_backup_vault_access_policy_response)

    # ACT
    response = BackupVaultAccessPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 2
    for resource in response:
        assert resource['DependencyType'] in [
            'aws:PrincipalOrgID',
            'aws:PrincipalOrgPaths',
            'aws:ResourceOrgID',
            'aws:ResourceOrgPaths'
        ]


def mock_backup(mocker,
                list_backup_vaults_response=None,
                get_backup_vault_access_policy_response=None):

    # ARRANGE
    if list_backup_vaults_response is None:
        list_backup_vaults_response = []

    if get_backup_vault_access_policy_response is None:
        get_backup_vault_access_policy_response = []

    def mock_list_backup_vaults(self):
        return list_backup_vaults_response

    mocker.patch(
        "aws.services.backup.Backup.list_backup_vaults",
        mock_list_backup_vaults
    )

    def mock_get_backup_vault_access_policy(self, backup_vault_name: str):
        return get_backup_vault_access_policy_response

    mocker.patch(
        "aws.services.backup.Backup.get_backup_vault_access_policy",
        mock_get_backup_vault_access_policy
    )
