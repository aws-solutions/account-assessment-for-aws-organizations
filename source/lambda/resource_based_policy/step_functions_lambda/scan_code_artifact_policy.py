# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_codeartifact.type_defs import DomainSummaryTypeDef, GetDomainPermissionsPolicyResultTypeDef, \
    RepositorySummaryTypeDef, GetRepositoryPermissionsPolicyResultTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.code_artifact import CodeArtifact
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class CodeArtifactPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        code_artifact_policies_with_org_dependency_in_all_regions = []
        self.logger.info(f"Scanning CodeArtifact Domain and Repository Policies in {region}")
        codeartifact_client = CodeArtifact(self.account_id, region)
        code_artifact_domains_with_org_dependency = self.scan_code_artifact_domain_policy(
            region,
            codeartifact_client)
        code_artifact_repositories_with_org_dependency = self.scan_code_artifact_repository_policy(
            region,
            codeartifact_client)
        code_artifact_policies_with_org_dependency = [
            *code_artifact_domains_with_org_dependency,
            *code_artifact_repositories_with_org_dependency
        ]
        code_artifact_policies_with_org_dependency_in_all_regions.extend(code_artifact_policies_with_org_dependency)
        return code_artifact_policies_with_org_dependency_in_all_regions

    def scan_code_artifact_domain_policy(self, region, codeartifact_client) -> Iterable[
        model.ResourceBasedPolicyResponseModel]:
        domain_data: list[model.CodeArtifactDomainData] = self._get_domain_data(codeartifact_client)
        domain_names_documents = self._get_domain_names_and_documents(domain_data, codeartifact_client)
        iam_policies_with_org_condition: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(
            domain_names_documents)
        return list(DenormalizeResourceBasedPolicyResponse(self.event).model(resource, region) for resource in
                    iam_policies_with_org_condition)

    def _get_domain_data(self, codeartifact_client) -> list[model.CodeArtifactDomainData]:
        domain_objects: list[DomainSummaryTypeDef] = codeartifact_client.list_domains()
        return list(self.denormalize_to_iam_domain_data(domain) for domain in domain_objects)

    @staticmethod
    def denormalize_to_iam_domain_data(domain: DomainSummaryTypeDef) -> model.CodeArtifactDomainData:
        data: model.CodeArtifactDomainData = {
            'name': domain['name']
        }
        return data

    @staticmethod
    def _get_domain_names_and_documents(
            domain_data: list[model.CodeArtifactDomainData], codeartifact_client) -> list[model.PolicyAnalyzerRequest]:
        domain_policies = []
        for domain in domain_data:
            domain_policy_document: GetDomainPermissionsPolicyResultTypeDef = \
                codeartifact_client.get_domain_permissions_policy(domain['name'])
            if domain_policy_document.get('policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    f"{domain['name']}#Domain",  # CodeArtifact Domain and Repository can have same name
                    domain_policy_document.get('policy').get('document')
                )
                domain_policies.append(policy_object)
        return domain_policies

    def scan_code_artifact_repository_policy(self, region,
                                             codeartifact_client) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        repository_data: list[model.CodeArtifactRepoData] = self._get_repository_data(codeartifact_client)
        repository_names_documents = self._get_repository_names_and_documents(repository_data, codeartifact_client)
        iam_policies_with_org_condition: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(
            repository_names_documents)
        return list(DenormalizeResourceBasedPolicyResponse(self.event).model(resource, region) for resource in
                    iam_policies_with_org_condition)

    def _get_repository_data(self, codeartifact_client) -> list[model.CodeArtifactRepoData]:
        repository_objects: list[RepositorySummaryTypeDef] = codeartifact_client.list_repositories()
        return list(self.denormalize_to_iam_repository_data(repository) for repository in repository_objects)

    @staticmethod
    def denormalize_to_iam_repository_data(repository: RepositorySummaryTypeDef) -> model.CodeArtifactRepoData:
        data: model.CodeArtifactRepoData = {
            'name': repository['name'],
            'domainName': repository['domainName']
        }
        return data

    @staticmethod
    def _get_repository_names_and_documents(
            repository_data: list[model.CodeArtifactRepoData],
            codeartifact_client) -> list[model.PolicyAnalyzerRequest]:
        repository_policies = []
        for repository in repository_data:
            repository_policy_document: GetRepositoryPermissionsPolicyResultTypeDef = \
                codeartifact_client.get_repository_permissions_policy(
                    repository['domainName'],
                    repository['name']
                )
            if repository_policy_document.get('policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    f"{repository['name']}#Repository",  # CodeArtifact Domain and Repository can have same name
                    repository_policy_document.get('policy').get('document')
                )
                repository_policies.append(policy_object)
        return repository_policies
