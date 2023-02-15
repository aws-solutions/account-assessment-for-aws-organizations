# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_kms.type_defs import KeyListEntryTypeDef, GetKeyPolicyResponseTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.key_management_service import KeyManagementService
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class KeyManagementServicePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning KMS Key Policies in {region}")
        kms_client = KeyManagementService(self.account_id, region)
        kms_keys: list[model.KMSData] = self._get_kms_keys(kms_client)
        kms_names_policies = self._get_kms_policy(kms_keys, kms_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(kms_names_policies)
        kms_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return kms_resources_for_region

    def _get_kms_keys(self, kms_client) -> list[model.KMSData]:
        kms_objects: list[KeyListEntryTypeDef] = kms_client.list_keys()
        return list(self.denormalize_to_kms_keys(kms_keys) for kms_keys in kms_objects)

    @staticmethod
    def denormalize_to_kms_keys(kms_keys: KeyListEntryTypeDef) -> model.KMSData:
        data: model.KMSData = {
            "KeyId": kms_keys['KeyId']
        }
        return data

    @staticmethod
    def _get_kms_policy(kms_keys: list[model.KMSData], kms_client) -> list[model.PolicyAnalyzerRequest]:
        kms_policies = []
        for key in kms_keys:
            policy: GetKeyPolicyResponseTypeDef = kms_client.get_key_policy(
                key.get('KeyId')
            )
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    key.get('KeyId'),
                    policy['Policy']
                )
                kms_policies.append(policy_object)
        return kms_policies
