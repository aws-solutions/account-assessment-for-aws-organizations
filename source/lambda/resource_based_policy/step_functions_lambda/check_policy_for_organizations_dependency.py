# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from aws_lambda_powertools import Logger
from mypy_boto3_serverlessrepo.type_defs import ApplicationPolicyStatementTypeDef
from os import getenv

from resource_based_policy.resource_based_policy_model import PolicyAnalyzerRequest, \
    PolicyAnalyzerResponse
from utils.list_utils import remove_none_values_from_the_list

AWS_RESOURCE_ORG_PATHS = "aws:ResourceOrgPaths"
AWS_RESOURCE_ORG_ID = "aws:ResourceOrgID"
AWS_PRINCIPAL_ORG_PATHS = "aws:PrincipalOrgPaths"
AWS_PRINCIPAL_ORG_ID = "aws:PrincipalOrgID"


class CheckForOrganizationsDependency:
    def __init__(self):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.resources_dependent_on_organizations = []

    def scan(self, policies: list[PolicyAnalyzerRequest]) -> list[PolicyAnalyzerResponse]:
        policies = remove_none_values_from_the_list(policies)
        for resource in policies:
            self.logger.debug(f"Checking for Organizations Dependency: {resource}")
            resource['Policy'] = self._update_policy_type_to_string_type(resource['Policy'])
            if "Condition" in resource['Policy']:  # Look for global context keys only if there is a Condition
                self.logger.debug(resource)
                self._check_for_principal_org_id(resource)
                self._check_for_principal_org_paths(resource)
                self._check_for_resource_org_id(resource)
                self._check_for_resource_org_paths(resource)

        response = [item for sub_item, item in enumerate(self.resources_dependent_on_organizations) if item not in
                    self.resources_dependent_on_organizations[sub_item + 1:]]
        return response

    @staticmethod
    def _update_policy_type_to_string_type(policy):
        if isinstance(policy, dict):
            return json.dumps(policy)  # handle IAM Policy API response returned in JSON format
        if isinstance(policy, str):
            return policy.replace("\\", '')  # remove extra backslash only present in API Gateway policies.

    def _check_for_principal_org_id(self, resource: PolicyAnalyzerRequest):
        if AWS_PRINCIPAL_ORG_ID.lower() in resource['Policy'].lower():
            self.logger.debug("Found PrincipalOrgID in the policy")
            self.process_statement_in_policy(resource)

    def _check_for_principal_org_paths(self, resource):
        if AWS_PRINCIPAL_ORG_PATHS.lower() in resource['Policy'].lower():
            self.logger.debug("Found PrincipalOrgPaths in the policy")
            self.process_statement_in_policy(resource)

    def _check_for_resource_org_id(self, resource):
        if AWS_RESOURCE_ORG_ID.lower() in resource['Policy'].lower():
            self.logger.debug("Found ResourceOrgID in the policy")
            self.process_statement_in_policy(resource)

    def _check_for_resource_org_paths(self, resource):
        if AWS_RESOURCE_ORG_PATHS.lower() in resource['Policy'].lower():
            self.logger.debug("Found ResourceOrgPaths in the policy")
            self.process_statement_in_policy(resource)

    def process_statement_in_policy(self, resource):
        self.logger.debug(resource)
        policy_statement = json.loads(resource['Policy']).get('Statement')
        self.logger.debug(f"Processing Policy Statement: {policy_statement}")
        if isinstance(policy_statement, list):
            self.logger.debug(f"Found Policy Statement in List Format")
            for statement in policy_statement:
                self.process_condition_in_statement(resource['ResourceName'], statement)
        if not isinstance(policy_statement, list):
            self.logger.debug(f"Found Policy Statement in String Format")
            self.process_condition_in_statement(resource['ResourceName'], policy_statement)

    def process_condition_in_statement(self, resource_name, statement):
        policy_condition = statement.get('Condition')
        # Condition Structure
        # "Condition" : { "{condition-operator}" : { "{condition-key}" : "{condition-value}" }}
        if policy_condition:
            for condition_operator, condition_key_value in policy_condition.items():
                self.logger.debug(f"Condition Operator: {condition_operator}")
                self.logger.debug(f"Condition Key Value: {condition_key_value}")
                for global_context_key, organizations_resource in condition_key_value.items():
                    if global_context_key.lower() in [
                        AWS_PRINCIPAL_ORG_ID.lower(),
                        AWS_PRINCIPAL_ORG_PATHS.lower(),
                        AWS_RESOURCE_ORG_ID.lower(),
                        AWS_RESOURCE_ORG_PATHS.lower()
                    ]:
                        policy_response: PolicyAnalyzerResponse = {
                            "ResourceName": resource_name,
                            "GlobalContextKey": global_context_key,
                            "OrganizationsResource": organizations_resource
                        }
                        self.resources_dependent_on_organizations.append(policy_response)


class CheckServerlessAppRepoForOrganizationsDependency:
    def __init__(self):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.resources_dependent_on_organizations = []

    def scan(self, policies: list[PolicyAnalyzerRequest]) -> list[PolicyAnalyzerResponse]:
        policies = remove_none_values_from_the_list(policies)
        for resource in policies:
            self.logger.debug(f"Checking for Organizations Dependency: {resource}")
            serverless_app_repo_statements: list[ApplicationPolicyStatementTypeDef] = \
                self._update_policy_type_to_dict_type(resource['Policy'])
            policies_with_dependencies = list(
                self._denormalize_to_policy_analyzer_response_model(
                    resource['ResourceName'],
                    statement) for statement in serverless_app_repo_statements)
            self.resources_dependent_on_organizations.extend(policies_with_dependencies)
        response = [item for sub_item, item in enumerate(self.resources_dependent_on_organizations) if item not in
                    self.resources_dependent_on_organizations[sub_item + 1:]]
        return remove_none_values_from_the_list(response)

    @staticmethod
    def _update_policy_type_to_dict_type(policy):
        if isinstance(policy, str):
            return json.loads(policy)
        if isinstance(policy, dict):
            return policy

    def _denormalize_to_policy_analyzer_response_model(
            self, resource_name, statement: ApplicationPolicyStatementTypeDef):
        if statement['PrincipalOrgIDs']:
            model: PolicyAnalyzerResponse = {
                'ResourceName': resource_name,
                'GlobalContextKey': AWS_PRINCIPAL_ORG_ID,
                'OrganizationsResource': ",".join(map(str, statement['PrincipalOrgIDs']))
            }
            self.logger.debug(model)
            return model
