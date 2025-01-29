#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_iam.type_defs import PolicyTypeDef as IAMPolicyTypeDef, PolicyVersionTypeDef, RoleTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.iam import IAM
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems


class IAMPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.iam_client = IAM(event['AccountId'])

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        try:
            iam_policies_dynamodb_items = self.scan_iam_policy()
            role_policy_dynamodb_items = self.scan_role_policy()
            return [
                *iam_policies_dynamodb_items,
                *role_policy_dynamodb_items
            ]
        except Exception as err:
            self.logger.error(err)
            self.logger.info(f"Error occurred while scanning IAM policies: {err}")
            raise err

    def scan_iam_policy(self) -> Iterable[model.DynamoDBPolicyItem]:
        policy_data: list[model.IAMPolicyData] = self._get_policy_data()
        policy_names_documents = self._get_iam_policy_names_and_documents(policy_data)
        policy_name_dynamodb_items = []
        for policy_name_document in policy_names_documents:
            if policy_name_document.get('Policy'):
                policy_name_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(policy_name_document))
        return policy_name_dynamodb_items

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
            self, policy_data: list[model.IAMPolicyData]) -> list[model.PolicyDetails]:
        iam_policies = []
        for policy in policy_data:
            resource_arn = policy.get('Arn')
            policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
            policy_details.update({'Region': 'GLOBAL'})
            policy_details.update({'PolicyType': model.PolicyType.IDENTITY_BASED_POLICY})
            policy_document: PolicyVersionTypeDef = self.iam_client.get_policy_version(
                policy.get('Arn'),
                policy.get('DefaultVersionId')
            )
            policy_details.update({'Policy': policy_document.get('Document')})
            iam_policies.append(policy_details)
        return iam_policies

    def scan_role_policy(self) -> Iterable[model.DynamoDBPolicyItem]:
        role_names_assume_role_policy_documents = self._get_role_names_and_assume_role_policy_documents()
        self.logger.debug(f"role policy line 75 {role_names_assume_role_policy_documents}")   
        role_names_assume_role_policy_dynamodb_items = []
        for role_name_assume_role_policy_document in role_names_assume_role_policy_documents:
            self.logger.debug(role_name_assume_role_policy_document)
            if role_name_assume_role_policy_document.get('Policy'):
                role_names_assume_role_policy_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event)
                                                                    .model(role_name_assume_role_policy_document))
        return role_names_assume_role_policy_dynamodb_items

    def _get_role_names_and_assume_role_policy_documents(self) -> list[model.PolicyDetails]:
        roles: list[RoleTypeDef] = self.iam_client.list_roles()

        role_names_role_policies = []
        for role in roles:
            resource_arn = f"{role.get('Arn')}/AssumeRolePolicyDocument"
            role_policies = get_policy_details_from_arn(resource_arn)
            role_policies.update({'Region': 'GLOBAL'})
            role_policies.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            role_policies.update({'Policy': role.get('AssumeRolePolicyDocument')})
            role_names_role_policies.append(role_policies)
            
            inline_policy_details = self._get_role_inline_policies(role)
            if inline_policy_details:
                role_names_role_policies.extend(inline_policy_details)
            
        return role_names_role_policies
        

    def _get_role_inline_policies(self, role: RoleTypeDef) -> list[model.PolicyDetails]:
        # get inline role policy names
        inline_policy_names = self.iam_client.list_role_inline_policies(role_name=role.get('RoleName'))
        inline_policy_details_list = []
        for inline_policy_name in inline_policy_names:
            # get inline policy details
            resource_arn = f"{role.get('Arn')}/inline-policy/{inline_policy_name}"
            inline_policy_details = get_policy_details_from_arn(resource_arn)
            get_role_policy_response = self.iam_client.get_role_policy(role_name=role.get('RoleName'), policy_name=inline_policy_name)
            inline_policy_details.update({'Region': 'GLOBAL'})
            inline_policy_details.update({'PolicyType': model.PolicyType.IDENTITY_BASED_POLICY})
            inline_policy_details.update({'Policy': get_role_policy_response.get('PolicyDocument')})
            inline_policy_details_list.append(inline_policy_details)
        return inline_policy_details_list