# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_ssm_incidents.type_defs import ResourcePolicyTypeDef, ResponsePlanSummaryTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.ssm_incidents import SSMIncidents
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class SSMIncidentsResponsePlanPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning SSM Incident Response Plan Policies in {region}")
        ssm_incidents_client = SSMIncidents(self.account_id, region)
        ssm_incidents_data: list[model.SSMIncidentsData] = self._get_response_plan_data(ssm_incidents_client)
        ssm_incidents_resource_policies = self._get_ssm_incidents_policies(ssm_incidents_data, ssm_incidents_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(ssm_incidents_resource_policies)
        ssm_incidents_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return ssm_incidents_resources_for_region

    def _get_response_plan_data(self, ssm_incidents_client) -> list[model.SSMIncidentsData]:
        ssm_incidents_objects: list[ResponsePlanSummaryTypeDef] = ssm_incidents_client.list_response_plans()
        return list(self.denormalize_to_ssm_incidents_data(ssm_incidents_data) for ssm_incidents_data in
                    ssm_incidents_objects)

    @staticmethod
    def denormalize_to_ssm_incidents_data(ssm_incidents_data: ResponsePlanSummaryTypeDef) -> model.SSMIncidentsData:
        data: model.SSMIncidentsData = {
            "arn": ssm_incidents_data['arn'],
            "name": ssm_incidents_data['name']
        }
        return data

    @staticmethod
    def _get_ssm_incidents_policies(
            ssm_incidents_data: list[model.SSMIncidentsData],
            ssm_incidents_client) -> list[model.PolicyAnalyzerRequest]:
        ssm_incidents_policies = []
        for response_plan in ssm_incidents_data:
            policies: list[ResourcePolicyTypeDef] = ssm_incidents_client.get_resource_policies(
                response_plan['arn']
            )
            for policy in policies:
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    f"{response_plan['name']}_{policy['policyId']}",
                    policy['policyDocument']
                )
                ssm_incidents_policies.append(policy_object)
        return ssm_incidents_policies
