# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_sns.type_defs import TopicTypeDef, GetTopicAttributesResponseTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.sns import SNS
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class SNSTopicPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning SNS Topic Policies in {region}")
        sns_client = SNS(self.account_id, region)
        topic_arns: list[TopicTypeDef] = sns_client.list_topics()
        topic_names_and_policies = self._get_topic_names_and_policies(topic_arns, sns_client)
        topic_policy_dynamodb_items = []
        for topic_name_and_policy in topic_names_and_policies:
            if topic_name_and_policy.get('Policy'):
                topic_policy_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event)
                                                   .model(topic_name_and_policy))
        return topic_policy_dynamodb_items

    def _get_topic_names_and_policies(
            self, topic_arns: list[TopicTypeDef], sns_client) -> list[model.PolicyDetails]:
        topic_names_and_policies = list(
            self._get_topic_policy(topic_arn['TopicArn'], sns_client) for topic_arn in topic_arns)
        self.logger.info(topic_names_and_policies)
        return topic_names_and_policies

    @staticmethod
    def _get_topic_policy(topic_arn: str, sns_client) -> model.PolicyDetails:
        topic_attributes: GetTopicAttributesResponseTypeDef = sns_client.get_topic_attributes(topic_arn)
        policy_details: model.PolicyDetails = get_policy_details_from_arn(topic_arn)
        policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
        policy_details.update({'Policy': topic_attributes.get('Attributes').get('Policy')})
        return policy_details
