# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_secretsmanager.type_defs import GetResourcePolicyResponseTypeDef, SecretListEntryTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.secrets_manager import SecretsManager
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class SecretsManagerPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning Policies attached to the Secrets in {region}")
        secrets_manager_client = SecretsManager(self.account_id, region)
        secrets_manager_data: list[model.SecretsManagerData] = self._get_secrets_manager_data(
            secrets_manager_client)
        secrets_manager_names_policies = self._get_secrets_manager_policy(secrets_manager_data,
                                                                          secrets_manager_client)
        secrets_manager_name_policy_dynamodb_items = []
        for secrets_manager_name_policy in secrets_manager_names_policies:
            if secrets_manager_name_policy.get('Policy'):
                secrets_manager_name_policy_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(secrets_manager_name_policy))
        return secrets_manager_name_policy_dynamodb_items

    def _get_secrets_manager_data(self, secrets_manager_client) -> list[model.SecretsManagerData]:
        secrets_manager_objects: list[SecretListEntryTypeDef] = secrets_manager_client.list_secrets()
        return list(self.denormalize_to_secrets_manager_data(secrets_manager_data) for secrets_manager_data in
                    secrets_manager_objects)

    @staticmethod
    def denormalize_to_secrets_manager_data(secrets_manager_data: SecretListEntryTypeDef) -> model.SecretsManagerData:
        data: model.SecretsManagerData = {
            "Name": secrets_manager_data['Name'],
            "Arn": secrets_manager_data['ARN']
        }
        return data

    @staticmethod
    def _get_secrets_manager_policy(secrets_manager_data: list[model.SecretsManagerData],
                                    secrets_manager_client) -> list[model.PolicyDetails]:
        secrets_manager_policies = []
        for secrets_manager in secrets_manager_data:
            resource_arn = secrets_manager.get('Arn')
            policy_details = get_policy_details_from_arn(resource_arn)
            policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            policy: GetResourcePolicyResponseTypeDef = secrets_manager_client.get_resource_policy(
                secrets_manager.get('Name')
            )
            policy_details.update({'Policy': policy.get('ResourcePolicy')})
            secrets_manager_policies.append(policy_details)
        return secrets_manager_policies
