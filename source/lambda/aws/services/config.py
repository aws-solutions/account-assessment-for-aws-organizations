#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv

from aws_lambda_powertools import Logger
from mypy_boto3_config.type_defs import DescribeOrganizationConfigRulesResponseTypeDef, OrganizationConfigRuleTypeDef, \
     GetCustomRulePolicyResponseTypeDef
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session


class Config:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('config', credentials=account_credentials, region=region)
        self.config_client = boto_session.get_client()

    @service_exception_handler
    def describe_organization_config_rules(self) -> list[OrganizationConfigRuleTypeDef]:
        response: DescribeOrganizationConfigRulesResponseTypeDef = self.config_client.describe_organization_config_rules()

        org_config_rules = response.get('OrganizationConfigRules', [])
        next_token = response.get('NextToken', None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.config_client.describe_organization_config_rules(
                NextToken=next_token
            )
            self.logger.info("Extending Config Rules List")
            org_config_rules.extend(response.get('OrganizationConfigRules', []))
            next_token = response.get('NextToken', None)

        return org_config_rules

    @resource_not_found_exception_handler
    def get_organization_custom_rule_policy(self, organization_config_rule_name: str) -> \
            GetCustomRulePolicyResponseTypeDef:
        response: GetCustomRulePolicyResponseTypeDef = self.config_client.get_organization_custom_rule_policy(
            OrganizationConfigRuleName=organization_config_rule_name
        )
        self.logger.debug(f"Config Policy: {response}")
        return response
