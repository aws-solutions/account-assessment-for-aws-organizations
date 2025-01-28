# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_lambda.type_defs import FunctionConfigurationTypeDef, GetPolicyResponseTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.lambda_functions import LambdaFunctions
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class LambdaFunctionPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning Lambda Function Policies in {region}")
        lambda_client = LambdaFunctions(self.account_id, region)
        lambda_function_data: list[model.LambdaFunctionData] = self._get_lambda_function_data(lambda_client)
        lambda_function_names_policies = self._get_lambda_function_policy(lambda_function_data, lambda_client)
        lambda_function_dynamodb_items = []
        for lambda_function_policy in lambda_function_names_policies:
            if lambda_function_policy.get('Policy'):
                lambda_function_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(
                    lambda_function_policy))

        return lambda_function_dynamodb_items

    def _get_lambda_function_data(self, lambda_client) -> list[model.LambdaFunctionData]:
        lambda_function_objects: list[FunctionConfigurationTypeDef] = lambda_client.list_functions()
        return list(self.denormalize_to_lambda_function_data(function_data) for function_data in
                    lambda_function_objects)

    @staticmethod
    def denormalize_to_lambda_function_data(function_data: FunctionConfigurationTypeDef) -> model.LambdaFunctionData:
        lambda_function_data: model.LambdaFunctionData = {
            "FunctionName": function_data['FunctionName'],
            "FunctionArn": function_data['FunctionArn']
        }
        return lambda_function_data

    @staticmethod
    def _get_lambda_function_policy(lambda_function_data: list[model.LambdaFunctionData],
                                    lambda_client) -> list[model.PolicyDetails]:
        lambda_policies = []
        for lambda_function in lambda_function_data:
            resource_arn = lambda_function.get('FunctionArn')
            policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
            policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            
            policy: GetPolicyResponseTypeDef = lambda_client.get_policy(
                lambda_function.get('FunctionName')
            )
            policy_details.update({'Policy': policy.get('Policy')})
            lambda_policies.append(policy_details)
        return lambda_policies
