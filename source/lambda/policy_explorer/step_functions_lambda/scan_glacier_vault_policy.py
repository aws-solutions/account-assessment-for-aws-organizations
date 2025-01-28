# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_glacier.type_defs import DescribeVaultOutputTypeDef, VaultAccessPolicyTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.s3 import Glacier
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class GlacierVaultPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']
    
    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.glacier_client = Glacier(self.account_id, region)
        vault_data = self._get_vault_data(self.glacier_client)
        vault_names_policies = self._get_vault_policies(vault_data, glacier_client=self.glacier_client)
        vault_policies_dynamodb_items = []
        for vault_name_policy in vault_names_policies:
            if vault_name_policy.get("Policy"):
                vault_policies_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(vault_name_policy))
        return vault_policies_dynamodb_items

    def _get_vault_data(self, glacier_client) -> list[model.GlacierVaultData]:
        vaults_data: list[DescribeVaultOutputTypeDef] = glacier_client.list_vaults()
        return list(self.denormalize_to_glacier_vault_data(vault_data) for vault_data in vaults_data)

    @staticmethod
    def denormalize_to_glacier_vault_data(vault_data: DescribeVaultOutputTypeDef) -> model.GlacierVaultData:
        data: model.GlacierVaultData = {
            "VaultName": vault_data['VaultName'],
            "VaultArn": vault_data['VaultARN']
        }
        return data

    def _get_vault_policies(self, vault_data: list[model.GlacierVaultData], glacier_client) -> list[model.PolicyDetails]:
        vault_policies = []
        for vault in vault_data:
            policy: VaultAccessPolicyTypeDef = glacier_client.get_vault_access_policy(vault.get("VaultName"))
            resource_arn = vault.get('VaultArn')
            policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
            policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            policy_details.update({'Policy': policy.get('Policy')})
            vault_policies.append(policy_details)
        return vault_policies
