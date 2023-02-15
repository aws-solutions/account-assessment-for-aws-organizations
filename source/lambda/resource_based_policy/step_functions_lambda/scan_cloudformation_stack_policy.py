# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_cloudformation.type_defs import StackSummaryTypeDef, GetStackPolicyOutputTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.cloud_formation import CloudFormation
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class CloudFormationStackPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Cloud Formation Stack Policies in {region}")
        cloudformation_client = CloudFormation(self.account_id, region)
        stack_summaries: list[StackSummaryTypeDef] = cloudformation_client.list_stacks()
        stack_names_and_policies = self._get_stack_names_and_policies(stack_summaries, cloudformation_client)
        self.logger.info(stack_names_and_policies)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(stack_names_and_policies)
        cloudformation_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return cloudformation_resources_for_region

    def _get_stack_names_and_policies(
            self, stack_summaries: list[StackSummaryTypeDef],
            cloudformation_client) -> list[model.PolicyAnalyzerRequest]:
        return list(self._get_stack_policies(summary['StackName'], cloudformation_client) for summary in
                    stack_summaries)

    @staticmethod
    def _get_stack_policies(stack_name: str, cloudformation_client) -> model.PolicyAnalyzerRequest:
        stack_policy: GetStackPolicyOutputTypeDef = cloudformation_client.get_stack_policy(stack_name)
        if stack_policy.get('StackPolicyBody'):
            policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                stack_name,
                stack_policy['StackPolicyBody']
            )
            return policy_object
