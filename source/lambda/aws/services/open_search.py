# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv

from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws_lambda_powertools import Logger
from mypy_boto3_opensearch.type_defs import ListDomainNamesResponseTypeDef, DescribeDomainsResponseTypeDef, \
    DomainInfoTypeDef, DomainStatusTypeDef


class OpenSearch:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('opensearch', credentials=account_credentials, region=region)
        self.opensearch_client = boto_session.get_client()

    @service_exception_handler
    def list_domain_names(self) -> list[DomainInfoTypeDef]:
        response: ListDomainNamesResponseTypeDef = self.opensearch_client.list_domain_names()
        return response.get('DomainNames', [])

    @resource_not_found_exception_handler
    def describe_domains(self, domain_names: list[str]) -> list[DomainStatusTypeDef]:
        response: DescribeDomainsResponseTypeDef = self.opensearch_client.describe_domains(
            DomainNames=domain_names
        )
        self.logger.debug(f"Domain Status List: {response}")
        return response.get('DomainStatusList', [])
