# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_sqs.type_defs import GetQueueAttributesResultTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.sqs import SQS
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions
from utils.string_manipulation import trim_string_split_to_list_get_last_item as get_name_from_arn


class SQSQueuePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning SQS Queue Policies in {region}")
        sqs_client = SQS(self.account_id, region)
        queue_urls = sqs_client.list_queues()
        queue_names_and_policies = self._get_queue_urls_and_policies(queue_urls, sqs_client)
        self.logger.info(queue_names_and_policies)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(queue_names_and_policies)
        sqs_resources_for_region = list(
            DenormalizeResourceBasedPolicyResponse(self.event).model(resource, region) for resource in
            resources_dependent_on_organizations)
        return sqs_resources_for_region

    def _get_queue_urls_and_policies(self, queue_urls: list[str], sqs_client) -> list[model.PolicyAnalyzerRequest]:
        return list(self._get_queue_policy(queue_url, sqs_client) for queue_url in queue_urls)

    @staticmethod
    def _get_queue_policy(queue_url: str, sqs_client) -> model.PolicyAnalyzerRequest:
        attribute_names = ['QueueArn', 'Policy']
        queue_attributes: GetQueueAttributesResultTypeDef = sqs_client.get_queue_attributes(
            queue_url,
            attribute_names
        )
        if queue_attributes.get('Attributes').get('Policy'):
            queue_name = get_name_from_arn(queue_attributes.get('Attributes').get('QueueArn'))
            policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                queue_name,
                queue_attributes.get('Attributes').get('Policy')
            )
            return policy_object
