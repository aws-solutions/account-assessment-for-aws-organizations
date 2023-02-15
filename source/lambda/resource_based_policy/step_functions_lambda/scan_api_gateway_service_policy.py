# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_apigateway.type_defs import RestApiResponseMetadataTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.api_gateway import APIGateway
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class APIGatewayPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning API Gateway Policies in {region}")
        apigateway_client = APIGateway(self.account_id, region)
        apigateway_names_policies: list[model.PolicyAnalyzerRequest] = self._get_apigateway_names_policies(
            apigateway_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(apigateway_names_policies)
        apigateway_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return apigateway_resources_for_region

    def _get_apigateway_names_policies(self, apigateway_client) -> list[model.PolicyAnalyzerRequest]:
        apigateway_objects: list[RestApiResponseMetadataTypeDef] = apigateway_client.get_rest_apis()
        return list(self.denormalize_to_apigateway_data(apigateway_data) for apigateway_data in apigateway_objects)

    @staticmethod
    def denormalize_to_apigateway_data(apigateway_data: RestApiResponseMetadataTypeDef) -> model.PolicyAnalyzerRequest:
        if apigateway_data.get('policy'):
            return DenormalizePolicyAnalyzerRequest().model(
                apigateway_data['name'],
                apigateway_data['policy']
            )
