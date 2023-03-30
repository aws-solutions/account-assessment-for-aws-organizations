# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_s3.type_defs import BucketTypeDef, GetBucketPolicyOutputTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.s3 import S3
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest
from resource_based_policy.supported_configuration.supported_regions_and_services import SupportedRegions


class S3BucketPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.s3_client = S3(event['AccountId'])

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        bucket_names = self._get_bucket_names()
        bucket_data: list[model.S3Data] = self._get_s3_data(bucket_names)
        bucket_names_policies = self._get_bucket_policies(bucket_data)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(bucket_names_policies)
        return list(DenormalizeResourceBasedPolicyResponse(self.event).model(resource) for resource in
                    resources_dependent_on_organizations)

    def _get_bucket_names(self) -> list[str]:
        bucket_objects: list[BucketTypeDef] = self.s3_client.list_buckets().get('Buckets', [])
        return [bucket.get('Name') for bucket in bucket_objects]

    def _get_s3_data(self, bucket_names) -> list[model.S3Data]:
        return list(self.denormalize_to_s3_data(bucket) for bucket in bucket_names)

    def denormalize_to_s3_data(self, bucket_name: str) -> model.S3Data:
        data: model.S3Data = {
            "BucketName": bucket_name,
            "BucketRegion": self.s3_client.get_bucket_location(bucket_name)
        }
        return data

    def _get_bucket_policies(self, s3_data: list[model.S3Data]) -> list[model.PolicyAnalyzerRequest]:
        bucket_names_policies = []
        for s3 in s3_data:
            s3_client = self._get_s3_client_with_regional_endpoint_if_opt_in_region(s3)
            policy: GetBucketPolicyOutputTypeDef = s3_client.get_bucket_policy(s3['BucketName'])
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    s3['BucketName'],
                    policy.get('Policy')
                )
                bucket_names_policies.append(policy_object)
        return bucket_names_policies

    def _get_s3_client_with_regional_endpoint_if_opt_in_region(self, s3):
        supported_regions = SupportedRegions().get_supported_region_objects(_event={}, _context={})
        for supported in supported_regions:
            if s3['BucketRegion'] == supported['Region'] and "Opt-In" in supported['RegionName']:
                return S3(self.event['AccountId'], s3['BucketRegion'])
        return self.s3_client
