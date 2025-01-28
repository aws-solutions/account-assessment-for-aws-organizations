# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_codebuild.type_defs import ProjectTypeDef, GetResourcePolicyOutputTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.code_build import CodeBuild
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn

class CodeBuildResourcePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning Code Build Resource Policies in {region}")
        code_build_client = CodeBuild(self.account_id, region)
        code_build_project_names = code_build_client.list_projects()
        code_build_project_data: list[model.CodeBuildData] = self._get_project_data(
            code_build_project_names,
            code_build_client
        ) if code_build_project_names else []
        code_built_report_group_data: list[model.CodeBuildData] = self._get_report_group_data(code_build_client)
        code_build_data = [*code_build_project_data, *code_built_report_group_data]
        code_build_resource_policies = self._get_code_build_resource_policies(code_build_data, code_build_client)
        resource_policies_for_dynamodb = []
        for code_build_resource in code_build_resource_policies:
            if code_build_resource.get("Policy"):
                resource_policies_for_dynamodb.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(code_build_resource))
       
        return resource_policies_for_dynamodb

    def _get_project_data(self, code_build_project_names, code_build_client) -> list[model.CodeBuildData]:
        code_build_project_objects: list[ProjectTypeDef] = code_build_client.batch_get_projects(
            code_build_project_names)
        return list(self.denormalize_to_code_build_project_data(code_build_data) for code_build_data in
                    code_build_project_objects)

    @staticmethod
    def denormalize_to_code_build_project_data(code_build_data: ProjectTypeDef) -> model.CodeBuildData:
        data: model.CodeBuildData = {
            "Arn": code_build_data['arn']
        }
        return data

    def _get_report_group_data(self, code_build_client) -> list[model.CodeBuildData]:
        code_built_report_group_arns = code_build_client.list_report_groups()
        return list(self.denormalize_to_code_build_report_group_data(report_group_arn) for report_group_arn in
                    code_built_report_group_arns)

    @staticmethod
    def denormalize_to_code_build_report_group_data(arn: str) -> model.CodeBuildData:
        data: model.CodeBuildData = {
            "Arn": arn
        }
        return data

    @staticmethod
    def _get_code_build_resource_policies(code_build_data: list[model.CodeBuildData], code_build_client) -> list[model.PolicyDetails]:
        code_build_policies = []
        for resource in code_build_data:
            resource_arn = resource['Arn']
            policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
            policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            policy: GetResourcePolicyOutputTypeDef = code_build_client.get_resource_policy(
                resource_arn
            )
            policy_details.update({'Policy': policy.get('policy')})
            code_build_policies.append(policy_details)
        return code_build_policies
