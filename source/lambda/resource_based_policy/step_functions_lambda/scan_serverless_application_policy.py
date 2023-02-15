# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_serverlessrepo.type_defs import ApplicationSummaryTypeDef, ApplicationPolicyStatementTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.serverless_application_repository import ServerlessApplicationRepository
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckServerlessAppRepoForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class ServerlessApplicationPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Serverless Application Policies in {region}")
        serverless_application_client = ServerlessApplicationRepository(self.account_id, region)
        serverless_application_data: list[model.ServerlessApplicationData] = self._get_applications_data(
            serverless_application_client)
        serverless_application_policies = self._get_serverless_application_policies(serverless_application_data,
                                                                                    serverless_application_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckServerlessAppRepoForOrganizationsDependency().scan(
            serverless_application_policies)
        serverless_application_policies_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return serverless_application_policies_for_region

    def _get_applications_data(self, serverless_application_client) -> list[model.ServerlessApplicationData]:
        serverless_application_objects: list[
            ApplicationSummaryTypeDef] = serverless_application_client.list_applications()
        return list(self.denormalize_to_serverless_application_data(serverless_application_data) for
                    serverless_application_data in serverless_application_objects)

    @staticmethod
    def denormalize_to_serverless_application_data(
            serverless_application_data: ApplicationSummaryTypeDef) -> model.ServerlessApplicationData:
        data: model.ServerlessApplicationData = {
            "ApplicationId": serverless_application_data['ApplicationId'],
            "Name": serverless_application_data['Name']
        }
        return data

    @staticmethod
    def _get_serverless_application_policies(serverless_application_data: list[model.ServerlessApplicationData],
                                             serverless_application_client) -> list[model.PolicyAnalyzerRequest]:
        serverless_application_policies = []
        for application in serverless_application_data:
            statements: list[ApplicationPolicyStatementTypeDef] = serverless_application_client.get_application_policy(
                application['ApplicationId']
            )
            if statements:
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    application['Name'],
                    json.dumps(statements)
                )
                serverless_application_policies.append(policy_object)
        return serverless_application_policies
