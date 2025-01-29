#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv

from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws_lambda_powertools import Logger
from mypy_boto3_codebuild.type_defs import GetResourcePolicyOutputTypeDef, ListProjectsOutputTypeDef, \
    BatchGetProjectsOutputTypeDef, ListSharedReportGroupsOutputTypeDef, ProjectTypeDef


class CodeBuild:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('codebuild', credentials=account_credentials, region=region)
        self.code_build_client = boto_session.get_client()

    @service_exception_handler
    def list_projects(self) -> list[str]:
        """
        :return:
        The list of build project names, with each build project name
        representing a single build project.
        """
        response: ListProjectsOutputTypeDef = self.code_build_client.list_projects(
            sortBy='NAME',
            sortOrder='ASCENDING'
        )

        projects = response.get('projects', [])
        next_token = response.get('nextToken', None)

        while next_token is not None:
            self.logger.debug(f"NextToken Returned: {next_token})")
            response = self.code_build_client.list_projects(
                sortBy='NAME',
                sortOrder='ASCENDING',
                nextToken=next_token
            )
            self.logger.info("Extending CodeBuild Project List")
            projects.extend(response.get('projects', []))
            next_token = response.get('nextToken', None)

        return projects

    @resource_not_found_exception_handler
    def batch_get_projects(self, names: list[str]) -> list[ProjectTypeDef]:
        response: BatchGetProjectsOutputTypeDef = self.code_build_client.batch_get_projects(
            names=names
        )
        self.logger.debug(f"Policy attached to the Code Build resource: {response}")
        return response.get('projects', [])

    @service_exception_handler
    def list_report_groups(self) -> list[str]:
        """
        :return:
        The list of ARNs for the report groups
        """
        response: ListSharedReportGroupsOutputTypeDef = self.code_build_client.list_report_groups(
            sortBy='NAME',
            sortOrder='ASCENDING'
        )

        report_groups = response.get('reportGroups', [])
        next_token = response.get('nextToken', None)

        while next_token is not None:
            self.logger.debug(f"NextToken Returned: {next_token})")
            response = self.code_build_client.list_report_groups(
                sortBy='NAME',
                sortOrder='ASCENDING',
                nextToken=next_token
            )
            self.logger.info("Extending CodeBuild Report Groups List")
            report_groups.extend(response.get('reportGroups', []))
            next_token = response.get('nextToken', None)

        return report_groups

    @resource_not_found_exception_handler
    def get_resource_policy(self, resource_arn: str) -> GetResourcePolicyOutputTypeDef:
        response = self.code_build_client.get_resource_policy(
            resourceArn=resource_arn
        )
        self.logger.debug(f"Policy attached to the Code Build resource: {response}")
        return response

