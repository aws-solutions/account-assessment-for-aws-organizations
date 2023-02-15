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


class S3BucketPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.s3_client = S3(event['AccountId'])

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        bucket_names = self._get_bucket_names()
        bucket_names_policies = self._get_bucket_policies(bucket_names)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(bucket_names_policies)
        return list(DenormalizeResourceBasedPolicyResponse(self.event).model(resource) for resource in
                    resources_dependent_on_organizations)

    def _get_bucket_names(self) -> list[str]:
        bucket_objects: list[BucketTypeDef] = self.s3_client.list_buckets().get('Buckets', [])
        return [bucket.get('Name') for bucket in bucket_objects]

    def _get_bucket_policies(self, bucket_names) -> list[model.PolicyAnalyzerRequest]:
        bucket_names_policies = []
        for bucket in bucket_names:
            policy: GetBucketPolicyOutputTypeDef = self.s3_client.get_bucket_policy(bucket)
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    bucket,
                    policy.get('Policy')
                )
                bucket_names_policies.append(policy_object)
        return bucket_names_policies
