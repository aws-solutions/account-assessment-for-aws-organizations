# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_ec2.type_defs import VpcEndpointTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.ec2 import EC2
from aws.utils.get_partition import partition_name_for_current_region
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions


class VPCEndpointsPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning VPC Endpoints Policies in {region}")
        ec2_client = EC2(self.account_id, region)
        vpc_endpoint_names_policies: list[model.PolicyAnalyzerRequest] = self._get_vpc_endpoint_names_policies(
            region, ec2_client)
        vpc_endpoint_policy_dynamodb_items = []
        for vpc_endpoint_policy in vpc_endpoint_names_policies:
            if vpc_endpoint_policy.get('Policy'):
                vpc_endpoint_policy_dynamodb_items.extend(
                    DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(vpc_endpoint_policy))
        return vpc_endpoint_policy_dynamodb_items

    def _get_vpc_endpoint_names_policies(self, region: str, ec2_client) -> list[model.PolicyDetails]:
        vpc_endpoint_objects: list[VpcEndpointTypeDef] = ec2_client.describe_vpc_endpoints()
        return list(self.denormalize_to_vpc_endpoint_data(region, vpc_endpoint_data) for vpc_endpoint_data in
                    vpc_endpoint_objects)

    def denormalize_to_vpc_endpoint_data(self, region: str, vpc_endpoint_data: VpcEndpointTypeDef) -> model.PolicyDetails:
        resource_arn = f"arn:{partition_name_for_current_region()}:vpc:{region}:{self.account_id}:endpoint/{vpc_endpoint_data['VpcEndpointId']}"
        policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
        policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
        policy_details.update({'Policy': vpc_endpoint_data.get('PolicyDocument')})
        policy_details.update({'Region': region})
        return policy_details
