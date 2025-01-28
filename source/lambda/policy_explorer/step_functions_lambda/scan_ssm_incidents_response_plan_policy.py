# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_ssm_incidents.type_defs import ResourcePolicyTypeDef, ResponsePlanSummaryTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.ssm_incidents import SSMIncidents
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class SSMIncidentsResponsePlanPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning SSM Incident Response Plan Policies in {region}")
        ssm_incidents_client = SSMIncidents(self.account_id, region)
        ssm_incidents_data: list[model.SSMIncidentsData] = self._get_response_plan_data(ssm_incidents_client)
        ssm_incidents_resource_policies = self._get_ssm_incidents_policies(region, ssm_incidents_data, ssm_incidents_client)
        ssm_incident_policy_dynamodb_items = []
        for ssm_incident_policy in ssm_incidents_resource_policies:
            if ssm_incident_policy.get('Policy'):
                ssm_incident_policy_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(ssm_incident_policy))

        return ssm_incident_policy_dynamodb_items

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

    def _get_ssm_incidents_policies(self, region,
            ssm_incidents_data: list[model.SSMIncidentsData],
            ssm_incidents_client) -> list[model.PolicyDetails]:
        ssm_incidents_policies = []
        for response_plan in ssm_incidents_data:

            policies: list[ResourcePolicyTypeDef] = ssm_incidents_client.get_resource_policies(
                response_plan['arn']
            )
            for policy in policies:
                policy_details: model.PolicyDetails = get_policy_details_from_arn(f"{response_plan['arn']}/{response_plan['name']}_{policy['policyId']}")
                policy_details.update({'Region': region})
                policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
                policy_details.update({'Policy': policy.get('policyDocument')})
                ssm_incidents_policies.append(policy_details)
        return ssm_incidents_policies
