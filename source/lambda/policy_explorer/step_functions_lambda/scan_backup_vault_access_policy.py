# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_backup.type_defs import BackupVaultListMemberTypeDef, GetBackupVaultAccessPolicyOutputTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.backup import Backup
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class BackupVaultAccessPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning Backup Vault Access Policies in {region}")
        backup_client = Backup(self.account_id, region)
        backup_data: list[model.BackupData] = self._get_backup_vault_data(
            backup_client)
        backup_policies = self._get_backup_policies(backup_data, backup_client)
        backup_policies_for_region = []
        for resource in backup_policies:
            if resource.get('Policy', None) is not None:
                backup_policies_for_region.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(resource))
        return backup_policies_for_region

    def _get_backup_vault_data(self, backup_client) -> list[model.BackupData]:
        backup_objects: list[
            BackupVaultListMemberTypeDef] = backup_client.list_backup_vaults()
        return list(self.denormalize_to_backup_data(backup_data) for
                    backup_data in backup_objects)

    @staticmethod
    def denormalize_to_backup_data(backup_data: BackupVaultListMemberTypeDef) -> model.BackupData:
        data: model.BackupData = {
            "BackupVaultName": backup_data['BackupVaultName'],
            "BackupVaultArn": backup_data['BackupVaultArn']
        }
        return data

    @staticmethod
    def _get_backup_policies(backup_data: list[model.BackupData],
                             backup_client) -> list[model.PolicyDetails]:
        backup_policies = []
        for vault in backup_data:
            policy: GetBackupVaultAccessPolicyOutputTypeDef = backup_client.get_backup_vault_access_policy(
                vault['BackupVaultName']
            )
            resource_arn = vault['BackupVaultArn']
            policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
            policy_details.update({'Policy': policy.get('Policy')})
            policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            backup_policies.append(policy_details)
        return backup_policies
