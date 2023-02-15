# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_sesv2.type_defs import IdentityInfoTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.simple_email_service_v2 import SimpleEmailServiceV2
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class SESIdentityPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning SES Identity Policies in {region}")
        ses_client = SimpleEmailServiceV2(self.account_id, region)
        ses_identity_data: list[IdentityInfoTypeDef] = ses_client.list_email_identities()
        ses_identities_policies = self._get_ses_policies(ses_identity_data, ses_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(ses_identities_policies)
        ses_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return ses_resources_for_region

    @staticmethod
    def _get_ses_policies(ses_data: list[IdentityInfoTypeDef], ses_client) -> list[model.PolicyAnalyzerRequest]:
        ses_policies = []
        for ses in ses_data:
            policies: dict[str, str] = ses_client.get_email_identity_policies(
                ses['IdentityName']
            ).get('Policies')

            # create a map for each policy per identity
            for policy_name, policy in policies.items():
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    f"{ses['IdentityName']}_{policy_name}",
                    policy
                )
                ses_policies.append(policy_object)
        return ses_policies
