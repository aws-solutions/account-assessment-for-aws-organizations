# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_config.type_defs import OrganizationConfigRuleTypeDef, GetCustomRulePolicyResponseTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.config import Config
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class ConfigRulePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning Config Rule Policies in {region}")
        config_client = Config(self.account_id, region)
        config_rules: list[model.ConfigData] = self._get_config_rules(config_client)
        config_rule_policies = self._get_config_rule_policies(config_rules, config_client)
        config_rule_policies_dynamodb_items = []
        for config_rule_policy in config_rule_policies:
            if config_rule_policy.get('Policy'):
                config_rule_policies_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(config_rule_policy))
        return config_rule_policies_dynamodb_items

    def _get_config_rules(self, config_client) -> list[model.ConfigData]:
        config_objects: list[OrganizationConfigRuleTypeDef] = config_client.describe_organization_config_rules()
        return list(self.denormalize_to_config_data(config_data) for config_data in config_objects)

    @staticmethod
    def denormalize_to_config_data(config_data: OrganizationConfigRuleTypeDef) -> model.ConfigData:
        data: model.ConfigData = {
            "OrganizationConfigRuleName": config_data['OrganizationConfigRuleName'],
            "OrganizationConfigRuleArn": config_data['OrganizationConfigRuleArn']
        }
        return data

    @staticmethod
    def _get_config_rule_policies(
            config_data: list[model.ConfigData], config_client) -> list[model.PolicyDetails]:
        config_policies = []
        for config in config_data:
            resource_arn = config.get('OrganizationConfigRuleArn')
            policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
            policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            policy: GetCustomRulePolicyResponseTypeDef = config_client.get_organization_custom_rule_policy(
                config['OrganizationConfigRuleName']
            )
            policy_details.update({'Policy': policy.get('PolicyText')})
            config_policies.append(policy_details)
        return config_policies
