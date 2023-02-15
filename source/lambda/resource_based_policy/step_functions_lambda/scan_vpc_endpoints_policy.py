# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_ec2.type_defs import VpcEndpointTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.ec2 import EC2
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class VPCEndpointsPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning VPC Endpoints Policies in {region}")
        ec2_client = EC2(self.account_id, region)
        vpc_endpoint_names_policies: list[model.PolicyAnalyzerRequest] = self._get_vpc_endpoint_names_policies(
            ec2_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(vpc_endpoint_names_policies)
        vpc_endpoint_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return vpc_endpoint_resources_for_region

    def _get_vpc_endpoint_names_policies(self, ec2_client) -> list[model.PolicyAnalyzerRequest]:
        vpc_endpoint_objects: list[VpcEndpointTypeDef] = ec2_client.describe_vpc_endpoints()
        return list(self.denormalize_to_vpc_endpoint_data(vpc_endpoint_data) for vpc_endpoint_data in
                    vpc_endpoint_objects)

    @staticmethod
    def denormalize_to_vpc_endpoint_data(vpc_endpoint_data: VpcEndpointTypeDef) -> model.PolicyAnalyzerRequest:
        if vpc_endpoint_data.get('PolicyDocument'):
            return DenormalizePolicyAnalyzerRequest().model(
                vpc_endpoint_data['VpcEndpointId'],
                vpc_endpoint_data['PolicyDocument']
            )
