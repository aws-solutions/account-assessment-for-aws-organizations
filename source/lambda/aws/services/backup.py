#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv


from aws_lambda_powertools import Logger
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler
from mypy_boto3_backup.type_defs import ListBackupVaultsOutputTypeDef, BackupVaultListMemberTypeDef, \
    GetBackupVaultAccessPolicyOutputTypeDef
from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session


class Backup:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('backup', credentials=account_credentials, region=region)
        self.backup_client = boto_session.get_client()

    @service_exception_handler
    def list_backup_vaults(self) -> list[BackupVaultListMemberTypeDef]:
        response: ListBackupVaultsOutputTypeDef = self.backup_client.list_backup_vaults()

        backup_vaults = response.get('BackupVaultList', [])
        next_token = response.get('NextToken', None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.backup_client.list_backup_vaults(
                NextToken=next_token
            )
            self.logger.info("Extending Backup Vault List")
            backup_vaults.extend(response.get('BackupVaultList', []))
            next_token = response.get('NextToken', None)

        return backup_vaults

    @resource_not_found_exception_handler
    def get_backup_vault_access_policy(self, backup_vault_name: str) -> GetBackupVaultAccessPolicyOutputTypeDef:
        response: GetBackupVaultAccessPolicyOutputTypeDef = self.backup_client.get_backup_vault_access_policy(
            BackupVaultName=backup_vault_name
        )
        self.logger.debug(f"Backup Vault Access Policy: {response}")
        return response

