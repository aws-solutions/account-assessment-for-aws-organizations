# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_sns.type_defs import TopicTypeDef, GetTopicAttributesResponseTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.sns import SNS
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions
from utils.string_manipulation import trim_string_split_to_list_get_last_item as get_name_from_arn


class SNSTopicPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning SNS Topic Policies in {region}")
        sns_client = SNS(self.account_id, region)
        topic_arns: list[TopicTypeDef] = sns_client.list_topics()
        topic_names_and_policies = self._get_topic_names_and_policies(topic_arns, sns_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(topic_names_and_policies)
        sns_resources_for_region = list(
            DenormalizeResourceBasedPolicyResponse(self.event).model(resource, region) for resource in
            resources_dependent_on_organizations)
        return sns_resources_for_region

    def _get_topic_names_and_policies(
            self, topic_arns: list[TopicTypeDef], sns_client) -> list[model.PolicyAnalyzerRequest]:
        topic_names_and_policies = list(
            self._get_topic_policy(topic_arn['TopicArn'], sns_client) for topic_arn in topic_arns)
        self.logger.info(topic_names_and_policies)
        return topic_names_and_policies

    @staticmethod
    def _get_topic_policy(topic_arn: str, sns_client) -> model.PolicyAnalyzerRequest:
        topic_attributes: GetTopicAttributesResponseTypeDef = sns_client.get_topic_attributes(topic_arn)
        if topic_attributes.get('Attributes').get('Policy'):
            topic_name = get_name_from_arn(topic_attributes.get('Attributes').get('TopicArn'))
            policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                topic_name,
                topic_attributes.get('Attributes').get('Policy')
            )
            return policy_object
