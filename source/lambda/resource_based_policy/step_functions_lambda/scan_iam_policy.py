# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_iam.type_defs import PolicyTypeDef as IAMPolicyTypeDef, PolicyVersionTypeDef, RoleTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.iam import IAM
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest


class IAMPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.iam_client = IAM(event['AccountId'])

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        iam_policies_with_org_dependency = self.scan_iam_policy()
        assumed_role_policy_with_org_dependency = self.scan_assume_role_policy()
        iam_resources_with_org_dependency = [
            *iam_policies_with_org_dependency,
            *assumed_role_policy_with_org_dependency
        ]
        return iam_resources_with_org_dependency

    def scan_iam_policy(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        policy_data: list[model.IAMPolicyData] = self._get_policy_data()
        policy_names_documents = self._get_iam_policy_names_and_documents(policy_data)
        iam_policies_with_org_condition: list[model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(
            policy_names_documents)
        return list(DenormalizeResourceBasedPolicyResponse(self.event).model(resource) for resource in
                    iam_policies_with_org_condition)

    def _get_policy_data(self) -> list[model.IAMPolicyData]:
        iam_policy_objects: list[IAMPolicyTypeDef] = self.iam_client.list_policies()
        return list(self.denormalize_to_iam_policy_data(policy) for policy in iam_policy_objects)

    @staticmethod
    def denormalize_to_iam_policy_data(policy: IAMPolicyTypeDef) -> model.IAMPolicyData:
        data: model.IAMPolicyData = {
            "Arn": policy['Arn'],
            "DefaultVersionId": policy['DefaultVersionId'],
            "PolicyName": policy['PolicyName']
        }
        return data

    def _get_iam_policy_names_and_documents(
            self, policy_data: list[model.IAMPolicyData]) -> list[model.PolicyAnalyzerRequest]:
        iam_policies = []
        for policy in policy_data:
            policy_document: PolicyVersionTypeDef = self.iam_client.get_policy_version(
                policy.get('Arn'),
                policy.get('DefaultVersionId')
            )
            if policy_document.get('Document'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    f"{policy['PolicyName']}#IAMPolicy",  # IAM Role and Policy can have same name
                    policy_document['Document']
                )
                iam_policies.append(policy_object)
        return iam_policies

    def scan_assume_role_policy(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        role_names_assume_role_policy_documents = self._get_role_names_and_assume_role_policy_documents()
        iam_policies_with_org_condition: list[model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(
            role_names_assume_role_policy_documents)
        return list(DenormalizeResourceBasedPolicyResponse(self.event).model(resource) for resource in
                    iam_policies_with_org_condition)

    def _get_role_names_and_assume_role_policy_documents(self) -> list[model.PolicyAnalyzerRequest]:
        roles: list[RoleTypeDef] = self.iam_client.list_roles()
        role_names_assume_role_policies = []
        for role in roles:
            if role.get('AssumeRolePolicyDocument'):
                role_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    f"{role['RoleName']}#IAMRole",  # IAM Role and Policy can have same name
                    role['AssumeRolePolicyDocument']
                )
                role_names_assume_role_policies.append(role_object)
        return role_names_assume_role_policies
