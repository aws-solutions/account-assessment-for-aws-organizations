# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_codebuild.type_defs import ProjectTypeDef, GetResourcePolicyOutputTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.code_build import CodeBuild
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions
from utils.string_manipulation import trim_string_split_to_list_get_last_item as get_name_from_arn, \
    trim_string_from_front


class CodeBuildResourcePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
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
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(code_build_resource_policies)
        code_build_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return code_build_resources_for_region

    def _get_project_data(self, code_build_project_names, code_build_client) -> list[model.CodeBuildData]:
        code_build_project_objects: list[ProjectTypeDef] = code_build_client.batch_get_projects(
            code_build_project_names)
        return list(self.denormalize_to_code_build_project_data(code_build_data) for code_build_data in
                    code_build_project_objects)

    @staticmethod
    def denormalize_to_code_build_project_data(code_build_data: ProjectTypeDef) -> model.CodeBuildData:
        data: model.CodeBuildData = {
            "arn": code_build_data['arn'],
            "name": code_build_data['name']
        }
        return data

    def _get_report_group_data(self, code_build_client) -> list[model.CodeBuildData]:
        code_built_report_group_arns = code_build_client.list_report_groups()
        return list(self.denormalize_to_code_build_report_group_data(report_group_arn) for report_group_arn in
                    code_built_report_group_arns)

    @staticmethod
    def denormalize_to_code_build_report_group_data(arn: str) -> model.CodeBuildData:
        data: model.CodeBuildData = {
            "arn": arn,
            "name": trim_string_from_front(
                get_name_from_arn(arn),
                remove='report-group/'
            )
        }
        return data

    @staticmethod
    def _get_code_build_resource_policies(
            code_build_data: list[model.CodeBuildData],
            code_build_client) -> list[model.PolicyAnalyzerRequest]:
        code_build_policies = []
        for resource in code_build_data:
            policy: GetResourcePolicyOutputTypeDef = code_build_client.get_resource_policy(
                resource['arn']
            )
            if policy.get('policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    resource['name'],
                    policy['policy']
                )
                code_build_policies.append(policy_object)
        return code_build_policies
