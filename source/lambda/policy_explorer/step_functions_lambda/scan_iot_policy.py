# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_iot.type_defs import PolicyTypeDef as IotPolicyTypeDef, GetPolicyResponseTypeDef as \
    IoTGetPolicyResponseTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.iot import IoT
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class IoTPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning IoT Policies in {region}")
        iot_client = IoT(self.account_id, region)
        iot_data: list[model.IoTData] = self._get_iot_data(iot_client)
        iot_names_policies = self._get_iot_policy(iot_data, iot_client, region)
        iot_resources_policies = []
        for iot_policy in iot_names_policies:
            if iot_policy.get('Policy'):
                iot_resources_policies.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(iot_policy))
        return iot_resources_policies

    def _get_iot_data(self, iot_client) -> list[model.IoTData]:
        iot_objects: list[IotPolicyTypeDef] = iot_client.list_policies()
        return list(self.denormalize_to_iot_data(iot_data) for iot_data in iot_objects)

    @staticmethod
    def denormalize_to_iot_data(iot_data: IotPolicyTypeDef) -> model.IoTData:
        data: model.IoTData = {
            "PolicyName": iot_data['policyName'],
            "PolicyArn": iot_data['policyArn']
        }
        return data

    @staticmethod
    def _get_iot_policy(iot_data: list[model.IoTData], iot_client, region) -> list[model.PolicyDetails]:
        iot_policies = []
        for iot in iot_data:
            resource_arn = iot.get("PolicyArn")
            policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
            policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            policy_details.update({'Region': region})
            policy: IoTGetPolicyResponseTypeDef = iot_client.get_policy(
                iot.get('PolicyName')
            )
            policy_details.update({'Policy': policy.get('policyDocument')})
            iot_policies.append(policy_details)
        return iot_policies
