# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_ecr.type_defs import GetRepositoryPolicyResponseTypeDef, RepositoryTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.ec2_container_registry import EC2ContainerRegistry
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class EC2ContainerRegistryRepositoryPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning ECR Repository Policies in {region}")
        ecr_client = EC2ContainerRegistry(self.account_id, region)
        ecr_data: list[model.ECRData] = self._get_ecr_data(ecr_client)
        ecr_repo_policies = self._get_ecr_policies(ecr_data, ecr_client)
        ecr_repo_policy_dynamodb_items = []
        for ecr_repo_policy in ecr_repo_policies:
            if ecr_repo_policy.get('Policy'):
                ecr_repo_policy_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(ecr_repo_policy))

        return ecr_repo_policy_dynamodb_items

    def _get_ecr_data(self, ecr_client) -> list[model.ECRData]:
        ecr_objects: list[RepositoryTypeDef] = ecr_client.describe_repositories()
        return list(self.denormalize_to_ecr_data(ecr_data) for ecr_data in ecr_objects)

    @staticmethod
    def denormalize_to_ecr_data(ecr_data: RepositoryTypeDef) -> model.ECRData:
        data: model.ECRData = {
            "RepositoryName": ecr_data['repositoryName'],
            "RepositoryArn": ecr_data['repositoryArn']
        }
        return data

    @staticmethod
    def _get_ecr_policies(ecr_data: list[model.ECRData], ecr_client) -> list[model.PolicyAnalyzerRequest]:
        ecr_policies = []
        for ecr in ecr_data:
            resource_arn = ecr['RepositoryArn']
            policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
            policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            policy: GetRepositoryPolicyResponseTypeDef = ecr_client.get_repository_policy(
                ecr['RepositoryName']
            )   
            policy_details.update({"Policy": policy.get('policyText', None)})
            ecr_policies.append(policy_details)
        return ecr_policies
