# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_cloudformation.type_defs import StackSummaryTypeDef, GetStackPolicyOutputTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.cloud_formation import CloudFormation
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions


class CloudFormationStackPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning Cloud Formation Stack Policies in {region}")
        cloudformation_client = CloudFormation(self.account_id, region)
        stack_summaries: list[StackSummaryTypeDef] = cloudformation_client.list_stacks()
        stack_names_and_policies = self._get_stack_names_and_policies(stack_summaries, cloudformation_client)
        self.logger.info(stack_names_and_policies)
        cloudformation_resources_for_region = []
        for resource in stack_names_and_policies:
            if resource.get('Policy', None):
                cloudformation_resources_for_region.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(resource))
        return cloudformation_resources_for_region

    def _get_stack_names_and_policies(
            self, stack_summaries: list[StackSummaryTypeDef],
            cloudformation_client) -> list[model.PolicyDetails]:
        return list(self._get_stack_policies({"Name":summary['StackName'], "Arn":summary['StackId']}, cloudformation_client) for summary in
                    stack_summaries)

    @staticmethod
    def _get_stack_policies(stack_data: model.CloudFormationData, cloudformation_client) -> model.PolicyDetails:
        stack_policy: GetStackPolicyOutputTypeDef = cloudformation_client.get_stack_policy(stack_data.get("Name"))
        resource_arn = stack_data.get('Arn')
        policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
        policy_details.update({'Policy': stack_policy.get('StackPolicyBody', None)})
        policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
        return policy_details
