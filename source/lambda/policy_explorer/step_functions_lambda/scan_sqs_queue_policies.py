# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_sqs.type_defs import GetQueueAttributesResultTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.sqs import SQS
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class SQSQueuePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning SQS Queue Policies in {region}")
        sqs_client = SQS(self.account_id, region)
        queue_urls = sqs_client.list_queues()
        queue_names_and_policies = self._get_queue_urls_and_policies(queue_urls, sqs_client)
        queue_policy_dynamodb_items = []
        for queue_name_and_policy in queue_names_and_policies:
            if queue_name_and_policy.get('Policy'):
                queue_policy_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event)
                                                    .model(queue_name_and_policy))  
        return queue_policy_dynamodb_items

    def _get_queue_urls_and_policies(self, queue_urls: list[str], sqs_client) -> list[model.PolicyDetails]:
        return list(self._get_queue_policy(queue_url, sqs_client) for queue_url in queue_urls)

    @staticmethod
    def _get_queue_policy(queue_url: str, sqs_client) -> model.PolicyDetails:
        attribute_names = ['QueueArn', 'Policy']
        queue_attributes: GetQueueAttributesResultTypeDef = sqs_client.get_queue_attributes(
            queue_url,
            attribute_names
        )
        policy_details: model.PolicyDetails = get_policy_details_from_arn(queue_attributes.get('Attributes').get('QueueArn'))
        policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
        policy_details.update({'Policy': queue_attributes.get('Attributes').get('Policy')}) 
        return policy_details
