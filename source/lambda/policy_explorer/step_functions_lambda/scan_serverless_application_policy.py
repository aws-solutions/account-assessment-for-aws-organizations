# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_serverlessrepo.type_defs import ApplicationSummaryTypeDef, ApplicationPolicyStatementTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.serverless_application_repository import ServerlessApplicationRepository
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from aws.utils.get_partition import partition_name_for_current_region
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class ServerlessApplicationPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning Serverless Application Policies in {region}")
        serverless_application_client = ServerlessApplicationRepository(self.account_id, region)
        serverless_application_data: list[model.ServerlessApplicationData] = self._get_applications_data(
            serverless_application_client, region)
        serverless_application_policies = self._get_serverless_application_policies(serverless_application_data,
                                                                                    serverless_application_client)
        serverless_repo_policy_dynamodb_items = []
        for serverless_repo_policy in serverless_application_policies:
            if serverless_repo_policy.get('Policy'):
                serverless_repo_policy_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(serverless_repo_policy))
        return serverless_repo_policy_dynamodb_items

    def _get_applications_data(self, serverless_application_client, region) -> list[model.ServerlessApplicationData]:
        serverless_application_objects: list[
            ApplicationSummaryTypeDef] = serverless_application_client.list_applications()
        return list(self.denormalize_to_serverless_application_data(serverless_application_data, region) for
                    serverless_application_data in serverless_application_objects)


    def denormalize_to_serverless_application_data(self, 
            serverless_application_data: ApplicationSummaryTypeDef, region: str) -> model.ServerlessApplicationData:
        data: model.ServerlessApplicationData = {
            "ApplicationId": serverless_application_data['ApplicationId'],
            "Name": serverless_application_data['Name'],
            "Region": region
        }
        return data


    def _get_serverless_application_policies(self, serverless_application_data: list[model.ServerlessApplicationData],
                                             serverless_application_client) -> list[model.PolicyDetails]:
        serverless_application_policies = []
        for application in serverless_application_data:
            resource_arn = f"arn:{partition_name_for_current_region()}:serverlessrepo:{application.get('Region')}:{self.account_id}:applications/{application.get('Name')}"
            policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
            policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            statements: list[ApplicationPolicyStatementTypeDef] = serverless_application_client.get_application_policy(
                application.get('ApplicationId')
            )
            if statements:
                policy_details.update({'Policy': {
                    'Version': '2012-10-17',
                    'Statement': statements
                }})
            
            serverless_application_policies.append(policy_details)
        return serverless_application_policies
