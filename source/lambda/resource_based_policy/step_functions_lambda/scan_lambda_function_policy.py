# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_lambda.type_defs import FunctionConfigurationTypeDef, GetPolicyResponseTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.lambda_functions import LambdaFunctions
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class LambdaFunctionPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Lambda Function Policies in {region}")
        lambda_client = LambdaFunctions(self.account_id, region)
        lambda_function_data: list[model.LambdaFunctionData] = self._get_lambda_function_data(lambda_client)
        lambda_function_names_policies = self._get_lambda_function_policy(lambda_function_data, lambda_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(lambda_function_names_policies)
        lambda_function_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return lambda_function_resources_for_region

    def _get_lambda_function_data(self, lambda_client) -> list[model.LambdaFunctionData]:
        lambda_function_objects: list[FunctionConfigurationTypeDef] = lambda_client.list_functions()
        return list(self.denormalize_to_lambda_function_data(function_data) for function_data in
                    lambda_function_objects)

    @staticmethod
    def denormalize_to_lambda_function_data(function_data: FunctionConfigurationTypeDef) -> model.LambdaFunctionData:
        lambda_function_data: model.LambdaFunctionData = {
            "FunctionName": function_data['FunctionName']
        }
        return lambda_function_data

    @staticmethod
    def _get_lambda_function_policy(lambda_function_data: list[model.LambdaFunctionData],
                                    lambda_client) -> list[model.PolicyAnalyzerRequest]:
        lambda_policies = []
        for lambda_function in lambda_function_data:
            policy: GetPolicyResponseTypeDef = lambda_client.get_policy(
                lambda_function.get('FunctionName')
            )
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    lambda_function.get('FunctionName'),
                    policy.get('Policy')
                )
                lambda_policies.append(policy_object)
        return lambda_policies
