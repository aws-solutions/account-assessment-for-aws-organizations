# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_organizations.type_defs import PolicySummaryTypeDef, DescribePolicyResponseTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.organizations import Organizations
from policy_explorer.step_functions_lambda.utils import  DenormalizePolicyDetailsIntoDynamoDBItems
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class ServiceControlPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event: model.ScanServiceRequestModel = event
        self.organizations_client = Organizations()

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        scp_resources = []
        try:
            service_control_policy_summaries: list[model.ServiceControlPolicySummary] = self.get_service_control_policy_summaries(self.organizations_client)
            scp_resources: list[model.PolicyDetails] = self.describe_policies(service_control_policy_summaries) 
            ddb_items: list[model.DynamoDBPolicyItem] = []
            for resource in scp_resources:
                if resource.get('Policy'):
                    ddb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(resource))
        except Exception as err:
            self.logger.info(f"Error occurred while scanning for Service Control Policies: {err}")
            raise err
        return ddb_items
    
    def get_service_control_policy_summaries(self, organizations_client: Organizations) -> list[model.ServiceControlPolicySummary]:
        service_control_policies: list[model.ServiceControlPolicySummary] = organizations_client.list_policies()
        return list(self.denormalize_to_service_control_policy_data(policy) for policy in service_control_policies)
            
    @staticmethod
    def denormalize_to_service_control_policy_data(policy: PolicySummaryTypeDef) -> model.ServiceControlPolicySummary:
        data: model.ServiceControlPolicySummary = {
            "Arn": policy['Arn'],
            "Id": policy['Id'],
        }
        return data

    def describe_policies(self, service_control_policy_summaries: list[model.ServiceControlPolicySummary]) -> list[model.PolicyDetails]:
        policies: list[model.PolicyDetails] = []
        for policy_summary in service_control_policy_summaries:
            policy_response: DescribePolicyResponseTypeDef = self.organizations_client.describe_policy(policy_summary.get('Id'))
            policy_details: model.PolicyDetails = get_policy_details_from_arn(policy_summary.get('Arn'))
            policy_details.update({'Region': 'GLOBAL'})
            policy_details.update({'PolicyType': model.PolicyType.SERVICE_CONTROL_POLICY})
            policy_details.update({'Policy': policy_response})
            policies.append(policy_details)
        return policies
        
        
