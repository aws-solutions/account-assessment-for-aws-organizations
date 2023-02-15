# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_backup.type_defs import BackupVaultListMemberTypeDef, GetBackupVaultAccessPolicyOutputTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.backup import Backup
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class BackupVaultAccessPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Backup Vault Access Policies in {region}")
        backup_client = Backup(self.account_id, region)
        backup_data: list[model.BackupData] = self._get_backup_vault_data(
            backup_client)
        backup_policies = self._get_backup_policies(backup_data, backup_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(backup_policies)
        backup_policies_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return backup_policies_for_region

    def _get_backup_vault_data(self, backup_client) -> list[model.BackupData]:
        backup_objects: list[
            BackupVaultListMemberTypeDef] = backup_client.list_backup_vaults()
        return list(self.denormalize_to_backup_data(backup_data) for
                    backup_data in backup_objects)

    @staticmethod
    def denormalize_to_backup_data(backup_data: BackupVaultListMemberTypeDef) -> model.BackupData:
        data: model.BackupData = {
            "BackupVaultName": backup_data['BackupVaultName']
        }
        return data

    @staticmethod
    def _get_backup_policies(backup_data: list[model.BackupData],
                             backup_client) -> list[model.PolicyAnalyzerRequest]:
        backup_policies = []
        for vault in backup_data:
            policy: GetBackupVaultAccessPolicyOutputTypeDef = backup_client.get_backup_vault_access_policy(
                vault['BackupVaultName']
            )
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    policy.get('BackupVaultName'),
                    policy.get('Policy')
                )
                backup_policies.append(policy_object)
        return backup_policies
