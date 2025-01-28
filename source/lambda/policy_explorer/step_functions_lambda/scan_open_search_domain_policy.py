# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_opensearch.type_defs import DomainInfoTypeDef, DomainStatusTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.open_search import OpenSearch
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from utils.list_utils import split_list_by_batch_size
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class OpenSearchDomainPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning OpenSearch Domain Policies in {region}")
        opensearch_client = OpenSearch(self.account_id, region)
        opensearch_domain_names: model.OpenSearchData = self._get_opensearch_domain_names(opensearch_client)
        opensearch_domain_policies = self._get_opensearch_domain_policies(opensearch_domain_names, opensearch_client)
        opensearch_domain_policy_dynamodb_items = []
        for opensearch_domain_policy in opensearch_domain_policies:
            if opensearch_domain_policy.get('Policy'):
                opensearch_domain_policy_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(opensearch_domain_policy))
        return opensearch_domain_policy_dynamodb_items

    def _get_opensearch_domain_names(self, opensearch_client) -> model.OpenSearchData:
        domain_objects: list[DomainInfoTypeDef] = opensearch_client.list_domain_names()
        return self.denormalize_to_opensearch_data(domain_objects)


    @staticmethod
    def denormalize_to_opensearch_data(domain_data: list[DomainInfoTypeDef]) -> model.OpenSearchData:
        domain_names = []
        for domain in domain_data:
            domain_names.append(domain['DomainName'])
        data: model.OpenSearchData = {
            "DomainNames": domain_names
        }
        return data

    @staticmethod
    def _get_opensearch_domain_policies(opensearch_data: model.OpenSearchData,
            opensearch_client) -> list[model.PolicyDetails]:
        opensearch_policies = []
        if opensearch_data.get('DomainNames'):
            # Describe API can process up to five specified OpenSearch Service domains
            chunked_domain_list = split_list_by_batch_size(opensearch_data.get('DomainNames'), 5)
            for domain_list in chunked_domain_list:
                domain_policies: list[DomainStatusTypeDef] = opensearch_client.describe_domains(
                    domain_list
                )
                for policy in domain_policies:
                    resource_arn = policy.get("ARN")
                    policy_details = get_policy_details_from_arn(resource_arn)
                    policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
                    policy_details.update({'Policy': policy.get('AccessPolicies')})
                    opensearch_policies.append(policy_details)
        return opensearch_policies
