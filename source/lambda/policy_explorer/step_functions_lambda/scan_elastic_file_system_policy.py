# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_efs.type_defs import FileSystemDescriptionTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.elastic_file_system import ElasticFileSystem
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class ElasticFileSystemPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning File System Policies in {region}")
        efs_client = ElasticFileSystem(self.account_id, region)
        file_system_id: list[model.EFSData] = self._get_file_system_id(efs_client)
        efs_names_policies = self._get_efs_policy(file_system_id, efs_client)
        efs_policy_dynamodb_items = []
        for efs_policy in efs_names_policies:
            if efs_policy.get("Policy"):
                efs_policy_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(efs_policy))
                
        return efs_policy_dynamodb_items

    def _get_file_system_id(self, efs_client) -> list[model.EFSData]:
        file_system_description: list[FileSystemDescriptionTypeDef] = efs_client.describe_file_systems()
        return list(self.denormalize_to_file_system_id(file_system_id) for file_system_id in
                    file_system_description)

    @staticmethod
    def denormalize_to_file_system_id(file_system_id: FileSystemDescriptionTypeDef) -> model.EFSData:
        data: model.EFSData = {
            "FileSystemId": file_system_id['FileSystemId'],
            "FileSystemArn": file_system_id['FileSystemArn']
        }
        return data

    @staticmethod
    def _get_efs_policy(file_system_id: list[model.EFSData], efs_client) -> list[model.PolicyAnalyzerRequest]:
        efs_policies = []
        for efs in file_system_id:
            resource_arn = efs.get('FileSystemArn')
            policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
            policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            policy: model.DescribeFileSystemPolicyResponse = efs_client.describe_file_system_policy(
                efs.get('FileSystemId')
            )
            policy_details.update({'Policy': policy.get('Policy', None)})
            efs_policies.append(policy_details)
        return efs_policies
