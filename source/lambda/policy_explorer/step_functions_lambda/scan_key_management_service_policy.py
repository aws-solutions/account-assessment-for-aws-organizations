# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_kms.type_defs import KeyListEntryTypeDef, GetKeyPolicyResponseTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.key_management_service import KeyManagementService
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class KeyManagementServicePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning KMS Key Policies in {region}")
        kms_client = KeyManagementService(self.account_id, region)
        kms_keys: list[model.KMSData] = self._get_kms_keys(kms_client)
        kms_names_policies = self._get_kms_policy(kms_keys, kms_client)
        kms_key_dynamodb_items = []
        for kms_policy in kms_names_policies:
            if kms_policy.get('Policy'):
                kms_key_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(kms_policy))
        
        return kms_key_dynamodb_items

    def _get_kms_keys(self, kms_client) -> list[model.KMSData]:
        kms_objects: list[KeyListEntryTypeDef] = kms_client.list_keys()
        return list(self.denormalize_to_kms_keys(kms_keys) for kms_keys in kms_objects)

    @staticmethod
    def denormalize_to_kms_keys(kms_keys: KeyListEntryTypeDef) -> model.KMSData:
        data: model.KMSData = {
            "KeyId": kms_keys['KeyId'],
            "KeyArn": kms_keys['KeyArn']
        }
        return data

    @staticmethod
    def _get_kms_policy(kms_keys: list[model.KMSData], kms_client) -> list[model.PolicyDetails]:
        kms_policies = []
        for key in kms_keys:
            resource_arn = key.get('KeyArn')
            policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
            policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            policy: GetKeyPolicyResponseTypeDef = kms_client.get_key_policy(
                key.get('KeyId')
            )
            policy_details.update({'Policy': policy.get('Policy')})
            kms_policies.append(policy_details)
        return kms_policies
