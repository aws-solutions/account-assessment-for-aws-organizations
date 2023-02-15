# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_secretsmanager.type_defs import GetResourcePolicyResponseTypeDef, SecretListEntryTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.secrets_manager import SecretsManager
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class SecretsManagerPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Policies attached to the Secrets in {region}")
        secrets_manager_client = SecretsManager(self.account_id, region)
        secrets_manager_data: list[model.SecretsManagerData] = self._get_secrets_manager_data(
            secrets_manager_client)
        secrets_manager_names_policies = self._get_secrets_manager_policy(secrets_manager_data,
                                                                          secrets_manager_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(secrets_manager_names_policies)
        secrets_manager_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return secrets_manager_resources_for_region

    def _get_secrets_manager_data(self, secrets_manager_client) -> list[model.SecretsManagerData]:
        secrets_manager_objects: list[SecretListEntryTypeDef] = secrets_manager_client.list_secrets()
        return list(self.denormalize_to_secrets_manager_data(secrets_manager_data) for secrets_manager_data in
                    secrets_manager_objects)

    @staticmethod
    def denormalize_to_secrets_manager_data(secrets_manager_data: SecretListEntryTypeDef) -> model.SecretsManagerData:
        data: model.SecretsManagerData = {
            "Name": secrets_manager_data['Name']
        }
        return data

    @staticmethod
    def _get_secrets_manager_policy(secrets_manager_data: list[model.SecretsManagerData],
                                    secrets_manager_client) -> list[model.PolicyAnalyzerRequest]:
        secrets_manager_policies = []
        for secrets_manager in secrets_manager_data:
            policy: GetResourcePolicyResponseTypeDef = secrets_manager_client.get_resource_policy(
                secrets_manager.get('Name')
            )
            if policy.get('ResourcePolicy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    secrets_manager.get('Name'),
                    policy['ResourcePolicy']
                )
                secrets_manager_policies.append(policy_object)
        return secrets_manager_policies
