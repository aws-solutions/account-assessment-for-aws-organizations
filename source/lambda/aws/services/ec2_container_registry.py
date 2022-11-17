# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv

from aws_lambda_powertools import Logger
from mypy_boto3_ecr.type_defs import DescribeRepositoriesResponseTypeDef, RepositoryTypeDef, \
    GetRepositoryPolicyResponseTypeDef
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session


class EC2ContainerRegistry:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('ecr', credentials=account_credentials, region=region)
        self.ecr_client = boto_session.get_client()

    @service_exception_handler
    def describe_repositories(self) -> list[RepositoryTypeDef]:
        response: DescribeRepositoriesResponseTypeDef = self.ecr_client.describe_repositories()

        repositories = response.get('repositories', [])
        next_token = response.get('nextToken', None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.ecr_client.describe_repositories(
                nextToken=next_token
            )
            self.logger.info("Extending Repository List")
            repositories.extend(response.get('repositories', []))
            next_token = response.get('nextToken', None)

        return repositories

    @resource_not_found_exception_handler
    def get_repository_policy(self, repository_name: str) -> GetRepositoryPolicyResponseTypeDef:
        response = self.ecr_client.get_repository_policy(
            repositoryName=repository_name
        )
        self.logger.debug(f"Repository Policy: {response}")
        return response



