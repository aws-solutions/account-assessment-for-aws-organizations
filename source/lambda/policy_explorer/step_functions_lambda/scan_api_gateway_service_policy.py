# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_apigateway.type_defs import RestApiResponseTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.api_gateway import APIGateway
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn
from aws.utils.get_partition import partition_name_for_current_region


class APIGatewayPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning API Gateway Policies in {region}")
        apigateway_client = APIGateway(self.account_id, region)
        apigateway_names_policies: list[model.PolicyDetails] = self._get_apigateway_names_policies(
            region, apigateway_client)
        apigateway_restapi_policies = []
        for resource in apigateway_names_policies:
            if resource.get('Policy', None) is not None:
                apigateway_restapi_policies.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(resource))
        return apigateway_restapi_policies

    def _get_apigateway_names_policies(self, region, apigateway_client):
        apigateway_objects: list[RestApiResponseTypeDef] = apigateway_client.get_rest_apis()
        return list(self.denormalize_to_apigateway_data(self.account_id, region, apigateway_data) for apigateway_data in apigateway_objects)

    @staticmethod
    def denormalize_to_apigateway_data(account_id: str, region: str, apigateway_data: RestApiResponseTypeDef) -> model.PolicyDetails:
        resource_arn = f"arn:{partition_name_for_current_region()}:apigateway:{region}::/restapis/{apigateway_data.get('id')}"
        policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
        policy_details.update({'Region': region})
        policy_details.update({'AccountId': account_id})
        policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
        policy_details.update({'Policy': apigateway_data.get('policy', None)})
        return policy_details
