# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_codeartifact.type_defs import DomainSummaryTypeDef, GetDomainPermissionsPolicyResultTypeDef, \
    RepositorySummaryTypeDef, GetRepositoryPermissionsPolicyResultTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.code_artifact import CodeArtifact
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class CodeArtifactPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        code_artifact_policies_in_all_regions = []
        self.logger.info(f"Scanning CodeArtifact Domain and Repository Policies in {region}")
        code_artifact_client = CodeArtifact(self.account_id, region)
        code_artifact_domain_policies = self.get_code_artifact_domain_policies(code_artifact_client)
        code_artifact_repository_policies = self.get_code_artifact_repository_policies(code_artifact_client)
        code_artifact_policies = [
            *code_artifact_domain_policies,
            *code_artifact_repository_policies
        ]
        code_artifact_policies_in_all_regions.extend(code_artifact_policies)
        return code_artifact_policies_in_all_regions

    def get_code_artifact_domain_policies(self, code_artifact_client) -> Iterable[model.DynamoDBPolicyItem]:
        domain_data: list[model.CodeArtifactDomainData] = self._get_domain_data(code_artifact_client)
        domain_names_documents = self._get_domain_names_and_documents(domain_data, code_artifact_client)
        domain_names_policies = []
        for domain_name_document in domain_names_documents:
            if domain_name_document.get('Policy', None):
                domain_names_policies.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(domain_name_document))
        
        return domain_names_policies


    def _get_domain_data(self, code_artifact_client) -> list[model.CodeArtifactDomainData]:
        domain_objects: list[DomainSummaryTypeDef] = code_artifact_client.list_domains()
        return list(self.denormalize_to_iam_domain_data(domain) for domain in domain_objects)

    @staticmethod
    def denormalize_to_iam_domain_data(domain: DomainSummaryTypeDef) -> model.CodeArtifactDomainData:
        data: model.CodeArtifactDomainData = {
            'Name': domain['name'],
            'Arn': domain['arn']
        }
        return data

    @staticmethod
    def _get_domain_names_and_documents(domain_data: list[model.CodeArtifactDomainData], code_artifact_client) -> list[model.PolicyDetails]:
        domain_policies = []
        for domain in domain_data:
            resource_arn = domain.get('Arn')
            policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
            policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            domain_policy_document: GetDomainPermissionsPolicyResultTypeDef = \
                code_artifact_client.get_domain_permissions_policy(domain['Name'])
            if domain_policy_document.get('policy'):
                policy_details.update({'Policy': domain_policy_document.get('policy').get('document')})
            domain_policies.append(policy_details)
        return domain_policies

    def get_code_artifact_repository_policies(self, code_artifact_client) -> Iterable[model.DynamoDBPolicyItem]:
        repository_data: list[model.CodeArtifactRepoData] = self._get_repository_data(code_artifact_client)
        repository_names_documents = self._get_repository_names_and_documents(repository_data, code_artifact_client)
        repository_policies  = []
        for repository_name_document in repository_names_documents:
            if repository_name_document.get('Policy', None):
                repository_policies.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(repository_name_document))
        return repository_policies

    def _get_repository_data(self, code_artifact_client) -> list[model.CodeArtifactRepoData]:
        repository_objects: list[RepositorySummaryTypeDef] = code_artifact_client.list_repositories()
        return list(self.denormalize_to_iam_repository_data(repository) for repository in repository_objects)

    @staticmethod
    def denormalize_to_iam_repository_data(repository: RepositorySummaryTypeDef) -> model.CodeArtifactRepoData:
        data: model.CodeArtifactRepoData = {
            'Name': repository['name'],
            'DomainName': repository['domainName'],
            'Arn': repository['arn']
        }
        return data

    @staticmethod
    def _get_repository_names_and_documents(
            repository_data: list[model.CodeArtifactRepoData],
            code_artifact_client) -> list[model.PolicyDetails]:
        repository_policies = []
        for repository in repository_data:
            resource_arn = repository.get('Arn')
            policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
            policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            repository_policy_document: GetRepositoryPermissionsPolicyResultTypeDef = \
                code_artifact_client.get_repository_permissions_policy(
                    repository['DomainName'],
                    repository['Name']
                )
            if repository_policy_document.get('policy'):
                    repository_policy_document.get('policy').get('document')
                    policy_details.update({'Policy': repository_policy_document.get('policy').get('document')})
            repository_policies.append(policy_details)
        return repository_policies
