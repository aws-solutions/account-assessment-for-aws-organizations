# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_efs.type_defs import FileSystemDescriptionTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.elastic_file_system import ElasticFileSystem
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class ElasticFileSystemPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning File System Policies in {region}")
        efs_client = ElasticFileSystem(self.account_id, region)
        file_system_id: list[model.EFSData] = self._get_file_system_id(efs_client)
        efs_names_policies = self._get_efs_policy(file_system_id, efs_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(efs_names_policies)
        efs_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return efs_resources_for_region

    def _get_file_system_id(self, efs_client) -> list[model.EFSData]:
        file_system_description: list[FileSystemDescriptionTypeDef] = efs_client.describe_file_systems()
        return list(self.denormalize_to_file_system_id(file_system_id) for file_system_id in
                    file_system_description)

    @staticmethod
    def denormalize_to_file_system_id(file_system_id: FileSystemDescriptionTypeDef) -> model.EFSData:
        data: model.EFSData = {
            "FileSystemId": file_system_id['FileSystemId']
        }
        return data

    @staticmethod
    def _get_efs_policy(file_system_id: list[model.EFSData], efs_client) -> list[model.PolicyAnalyzerRequest]:
        efs_policies = []
        for efs in file_system_id:
            policy: model.DescribeFileSystemPolicyResponse = efs_client.describe_file_system_policy(
                efs.get('FileSystemId')
            )
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    policy['FileSystemId'],
                    policy['Policy']
                )
                efs_policies.append(policy_object)
        return efs_policies
