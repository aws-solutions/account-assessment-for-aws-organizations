# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_glacier.type_defs import DescribeVaultOutputTypeDef, VaultAccessPolicyTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.s3 import Glacier
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest


class GlacierVaultPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.glacier_client = Glacier(event['AccountId'])

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        vault_names = self._get_vault_names()
        vault_names_policies = self._get_vault_policies(vault_names)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(vault_names_policies)
        return list(DenormalizeResourceBasedPolicyResponse(self.event).model(resource) for resource in
                    resources_dependent_on_organizations)

    def _get_vault_names(self) -> list[str]:
        vault_name: list[DescribeVaultOutputTypeDef] = self.glacier_client.list_vaults()
        return [vault.get('VaultName') for vault in vault_name]

    def _get_vault_policies(self, vault_names) -> list[model.PolicyAnalyzerRequest]:
        vault_names_policies = []
        for vault in vault_names:
            policy: VaultAccessPolicyTypeDef = self.glacier_client.get_vault_access_policy(vault)
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    vault,
                    policy.get('Policy')
                )
                vault_names_policies.append(policy_object)
        return vault_names_policies
