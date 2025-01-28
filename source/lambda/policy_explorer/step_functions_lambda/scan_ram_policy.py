# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_ram.type_defs import ResourceTypeDef, GetResourcePoliciesResponseTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.ram import RAM
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions 


class RAMPolicy:
    def __init__(self, event: model.ScanServiceRequestModel) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger = Logger(service=self.__class__.__name__, level=getenv("LOG_LEVEL"))
        self.event: model.ScanServiceRequestModel = event
        self.account_id: str = event["AccountId"]

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning RAM Policies in {region}")
        ram_client = RAM(self.account_id, region)
        resources: list[ResourceTypeDef] = ram_client.list_resources()
        resources_and_policies: list[model.PolicyDetails] = self._get_resources_and_policies(region, resources, ram_client)
        resource_policy_dynamodb_items = []
        for resource_policy in resources_and_policies:
            if resource_policy.get("Policy"):
                resource_policy_dynamodb_items.extend(
                    DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(resource_policy)
                )

        return resource_policy_dynamodb_items

    def _get_resources_and_policies(self, region: str, resources: list[ResourceTypeDef], ram_client: RAM) -> list[model.PolicyDetails]:
        # ram resource_arns response has duplicates as same resource can be shared in multiple ram shares remove duplicates to reduce api's
        resource_arn_set: set = set()
        for resource in resources:
            resource_arn_set.add(resource.get('arn'))
        return list(
            self._get_ram_policies(region, resource, ram_client) for resource in resource_arn_set
        )

    def _get_ram_policies(self, region: str, resource_arn: str, ram_client: RAM) -> model.PolicyDetails:
        resource_policy: str = ram_client.get_resource_policy(resource_arn)
        policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
        policy_details.update({"Policy": resource_policy})
        policy_details.update({"PolicyType": model.PolicyType.RESOURCE_BASED_POLICY})
        policy_details.update({"Region": region})
        return policy_details