# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_glue.type_defs import GluePolicyTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.glue import Glue
from aws.utils.get_partition import partition_name_for_current_region
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions


class GlueResourcePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning Glue Resource Policies in {region}")
        glue_client = Glue(self.account_id, region)
        glue_names_policies: list[model.PolicyAnalyzerRequest] = self._get_glue_data(region, glue_client)
        glue_policy_dynamodb_items = []
        for glue_name_policy in glue_names_policies:
            if glue_name_policy.get('Policy'):
                glue_policy_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event)
                                                   .model(glue_name_policy))

        return glue_policy_dynamodb_items

    def _get_glue_data(self, region, glue_client) -> list[model.PolicyAnalyzerRequest]:
        glue_objects: list[GluePolicyTypeDef] = glue_client.get_resource_policies()
        return list(self.denormalize_to_glue_data(region, glue_data) for glue_data in glue_objects)

    def denormalize_to_glue_data(self, region: str, glue_data: GluePolicyTypeDef) -> model.PolicyDetails:
        resource_arn = f"arn:{partition_name_for_current_region()}:glue:{region}:{self.account_id}:policy/{glue_data['PolicyHash']}"
        policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
        policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
        policy_details.update({'Policy': glue_data.get('PolicyInJson')})
        return policy_details
