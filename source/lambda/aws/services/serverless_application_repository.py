# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv


from aws_lambda_powertools import Logger
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler
from mypy_boto3_serverlessrepo.type_defs import ListApplicationsResponseTypeDef, ApplicationSummaryTypeDef, \
    GetApplicationPolicyResponseTypeDef, ApplicationPolicyStatementTypeDef

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session


class ServerlessApplicationRepository:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('serverlessrepo', credentials=account_credentials, region=region)
        self.serverlessrepo_client = boto_session.get_client()

    @service_exception_handler
    def list_applications(self) -> list[ApplicationSummaryTypeDef]:
        response: ListApplicationsResponseTypeDef = self.serverlessrepo_client.list_applications()

        applications = response.get('Applications', [])
        next_token = response.get('NextToken', None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.serverlessrepo_client.list_applications(
                NextToken=next_token
            )
            self.logger.info("Extending Applications List")
            applications.extend(response.get('Applications', []))
            next_token = response.get('NextToken', None)

        self.logger.debug(f"Applications: {response}")
        return applications

    @resource_not_found_exception_handler
    def get_application_policy(self, application_id: str) -> list[ApplicationPolicyStatementTypeDef]:
        response: GetApplicationPolicyResponseTypeDef = self.serverlessrepo_client.get_application_policy(
            ApplicationId=application_id
        )
        self.logger.debug(f"Application Policy: {response}")
        return response.get('Statements', [])

