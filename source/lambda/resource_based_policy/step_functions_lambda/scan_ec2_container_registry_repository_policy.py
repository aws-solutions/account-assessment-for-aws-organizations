# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_ecr.type_defs import GetRepositoryPolicyResponseTypeDef, RepositoryTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.ec2_container_registry import EC2ContainerRegistry
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class EC2ContainerRegistryRepositoryPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning ECR Repository Policies in {region}")
        ecr_client = EC2ContainerRegistry(self.account_id, region)
        ecr_data: list[model.ECRData] = self._get_ecr_data(ecr_client)
        ecr_repo_policies = self._get_ecr_policies(ecr_data, ecr_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(ecr_repo_policies)
        ecr_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return ecr_resources_for_region

    def _get_ecr_data(self, ecr_client) -> list[model.ECRData]:
        ecr_objects: list[RepositoryTypeDef] = ecr_client.describe_repositories()
        return list(self.denormalize_to_ecr_data(ecr_data) for ecr_data in ecr_objects)

    @staticmethod
    def denormalize_to_ecr_data(ecr_data: RepositoryTypeDef) -> model.ECRData:
        data: model.ECRData = {
            "repositoryName": ecr_data['repositoryName']
        }
        return data

    @staticmethod
    def _get_ecr_policies(ecr_data: list[model.ECRData], ecr_client) -> list[model.PolicyAnalyzerRequest]:
        ecr_policies = []
        for ecr in ecr_data:
            policy: GetRepositoryPolicyResponseTypeDef = ecr_client.get_repository_policy(
                ecr['repositoryName']
            )
            if policy.get('policyText'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    policy['repositoryName'],
                    policy['policyText']
                )
                ecr_policies.append(policy_object)
        return ecr_policies
