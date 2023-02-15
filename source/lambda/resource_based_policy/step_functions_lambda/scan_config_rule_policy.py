# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_config.type_defs import OrganizationConfigRuleTypeDef, GetCustomRulePolicyResponseTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.config import Config
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class ConfigRulePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Config Rule Policies in {region}")
        config_client = Config(self.account_id, region)
        config_rules: list[model.ConfigData] = self._get_config_rules(config_client)
        config_rule_policies = self._get_config_rule_policies(config_rules, config_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(config_rule_policies)
        config_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return config_resources_for_region

    def _get_config_rules(self, config_client) -> list[model.ConfigData]:
        config_objects: list[OrganizationConfigRuleTypeDef] = config_client.describe_organization_config_rules()
        return list(self.denormalize_to_config_data(config_data) for config_data in config_objects)

    @staticmethod
    def denormalize_to_config_data(config_data: OrganizationConfigRuleTypeDef) -> model.ConfigData:
        data: model.ConfigData = {
            "OrganizationConfigRuleName": config_data['OrganizationConfigRuleName']
        }
        return data

    @staticmethod
    def _get_config_rule_policies(
            config_data: list[model.ConfigData], config_client) -> list[model.PolicyAnalyzerRequest]:
        config_policies = []
        for config in config_data:
            policy: GetCustomRulePolicyResponseTypeDef = config_client.get_organization_custom_rule_policy(
                config['OrganizationConfigRuleName']
            )
            if policy.get('PolicyText'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    config['OrganizationConfigRuleName'],
                    policy['PolicyText']
                )
                config_policies.append(policy_object)
        return config_policies
