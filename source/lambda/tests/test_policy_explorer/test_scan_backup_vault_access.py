#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import datetime
from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_backup.type_defs import BackupVaultListMemberTypeDef, GetBackupVaultAccessPolicyOutputTypeDef

from policy_explorer.policy_explorer_model import PolicyType
from policy_explorer.step_functions_lambda.scan_backup_vault_access_policy import BackupVaultAccessPolicy
from tests.test_policy_explorer.mock_data import event

logger = Logger(level='info', service="test_code_build")


@mock_aws
def test_mock_backup_scan_policy_no_policies(mocker):
    # ARRANGE
    mock_backup(mocker)

    # ARRANGE
    response = BackupVaultAccessPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_aws
def test_mock_backup_scan_policy(mocker):
    # ARRANGE
    list_backup_vaults_response: list[BackupVaultListMemberTypeDef] = [
        {
            "BackupVaultName": "mock_name",
            "BackupVaultArn": "arn:aws:backup:us-east-2:111111111111:backup-vault:mock_name",
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
        "BackupVaultArn": "arn:aws:backup:us-east-2:111111111111:backup-vault:mock_name",
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
    assert response[0]['PartitionKey'] == PolicyType.RESOURCE_BASED_POLICY.value
    assert response[0]['Condition'] == '{\"StringEquals\": {\"aws:PrincipalOrgID\": \"o-a1b2c3d4e5\"}}'


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
