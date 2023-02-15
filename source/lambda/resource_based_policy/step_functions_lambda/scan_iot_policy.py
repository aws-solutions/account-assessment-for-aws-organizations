# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_iot.type_defs import PolicyTypeDef as IotPolicyTypeDef, GetPolicyResponseTypeDef as \
    IoTGetPolicyResponseTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.iot import IoT
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class IoTPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning IoT Policies in {region}")
        iot_client = IoT(self.account_id, region)
        iot_data: list[model.IoTData] = self._get_iot_data(iot_client)
        iot_names_policies = self._get_iot_policy(iot_data, iot_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(iot_names_policies)
        iot_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return iot_resources_for_region

    def _get_iot_data(self, iot_client) -> list[model.IoTData]:
        iot_objects: list[IotPolicyTypeDef] = iot_client.list_policies()
        return list(self.denormalize_to_iot_data(iot_data) for iot_data in iot_objects)

    @staticmethod
    def denormalize_to_iot_data(iot_data: IotPolicyTypeDef) -> model.IoTData:
        data: model.IoTData = {
            "policyName": iot_data['policyName']
        }
        return data

    @staticmethod
    def _get_iot_policy(iot_data: list[model.IoTData], iot_client) -> list[model.PolicyAnalyzerRequest]:
        iot_policies = []
        for iot in iot_data:
            policy: IoTGetPolicyResponseTypeDef = iot_client.get_policy(
                iot.get('policyName')
            )
            if policy.get('policyDocument'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    iot.get('policyName'),
                    policy['policyDocument']
                )
                iot_policies.append(policy_object)
        return iot_policies
