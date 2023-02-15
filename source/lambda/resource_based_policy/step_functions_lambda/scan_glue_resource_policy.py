# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_glue.type_defs import GluePolicyTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.glue import Glue
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class GlueResourcePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Glue Resource Policies in {region}")
        glue_client = Glue(self.account_id, region)
        glue_names_policies: list[model.PolicyAnalyzerRequest] = self._get_glue_data(glue_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(glue_names_policies)
        glue_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return glue_resources_for_region

    def _get_glue_data(self, glue_client) -> list[model.PolicyAnalyzerRequest]:
        glue_objects: list[GluePolicyTypeDef] = glue_client.get_resource_policies()
        return list(self.denormalize_to_glue_data(glue_data) for glue_data in glue_objects)

    @staticmethod
    def denormalize_to_glue_data(glue_data: GluePolicyTypeDef) -> model.PolicyAnalyzerRequest:
        if glue_data.get('PolicyInJson'):
            return DenormalizePolicyAnalyzerRequest().model(
                glue_data['PolicyHash'],
                glue_data['PolicyInJson']
            )
