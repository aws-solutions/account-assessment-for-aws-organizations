#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv


from aws_lambda_powertools import Logger
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler
from mypy_boto3_codeartifact.type_defs import ListDomainsResultTypeDef, DomainSummaryTypeDef, \
    ListRepositoriesResultTypeDef, RepositorySummaryTypeDef, GetDomainPermissionsPolicyResultTypeDef, \
    GetRepositoryPermissionsPolicyResultTypeDef
from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session


class CodeArtifact:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('codeartifact', credentials=account_credentials, region=region)
        self.codeartifact_client = boto_session.get_client()

    @service_exception_handler
    def list_domains(self) -> list[DomainSummaryTypeDef]:
        response: ListDomainsResultTypeDef = self.codeartifact_client.list_domains()

        domains = response.get('domains', [])
        next_token = response.get('nextToken', None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.codeartifact_client.list_domains(
                nextToken=next_token
            )
            self.logger.info("Extending CodeArtifact Domains List")
            domains.extend(response.get('domains', []))
            next_token = response.get('nextToken', None)
        self.logger.debug(f"CodeArtifact Domains: {domains}")
        return domains

    @service_exception_handler
    def list_repositories(self) -> list[RepositorySummaryTypeDef]:
        response: ListRepositoriesResultTypeDef = self.codeartifact_client.list_repositories()

        repositories = response.get('repositories', [])
        next_token = response.get('nextToken', None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.codeartifact_client.list_repositories(
                nextToken=next_token
            )
            self.logger.info("Extending CodeArtifact Repository List")
            repositories.extend(response.get('repositories', []))
            next_token = response.get('nextToken', None)
        self.logger.debug(f"CodeArtifact Repositories: {repositories}")
        return repositories

    @resource_not_found_exception_handler
    def get_domain_permissions_policy(self, domain_name: str) -> GetDomainPermissionsPolicyResultTypeDef:
        response: GetDomainPermissionsPolicyResultTypeDef = self.codeartifact_client.get_domain_permissions_policy(
            domain=domain_name
        )
        self.logger.debug(f"CodeArtifact Domain Policies: {response}")
        return response

    @resource_not_found_exception_handler
    def get_repository_permissions_policy(
            self, domain_name: str,
            repository_name: str) -> GetRepositoryPermissionsPolicyResultTypeDef:
        response: GetRepositoryPermissionsPolicyResultTypeDef = \
            self.codeartifact_client.get_repository_permissions_policy(
                domain=domain_name,
                repository=repository_name
            )
        self.logger.debug(f"CodeArtifact Repository Policies: {response}")
        return response

