# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv

from botocore.exceptions import ClientError

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws_lambda_powertools import Logger
from mypy_boto3_iam.type_defs import PolicyTypeDef, PolicyVersionTypeDef, GetPolicyVersionResponseTypeDef,  \
    ListPoliciesResponseTypeDef, ListRolesResponseTypeDef, RoleTypeDef


class IAM:
    def __init__(self, account_id):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('iam', credentials=account_credentials)
        self.iam_client = boto_session.get_client()

    def list_policies(self) -> list[PolicyTypeDef]:
        try:
            response: ListPoliciesResponseTypeDef = self.iam_client.list_policies(
                Scope='Local'  # list only the customer managed policies in an account
            )
            policies = response.get('Policies', [])
            is_truncated = response.get('IsTruncated', False)
            marker = response.get('Marker')

            while is_truncated is True:
                self.logger.debug(f"Is truncated - marker: {marker})")
                response = self.iam_client.list_policies(
                    Scope='Local',  # list only the customer managed policies in an account
                    Marker=marker,
                )
                self.logger.info("Extending IAM Policy List")
                policies.extend(response.get('Policies', []))
                is_truncated = response.get('IsTruncated')
                marker = response.get('Marker')

            self.logger.debug(f"Policies: {policies}")
            return policies
        except ClientError as err:
            self.logger.error(err)
            raise

    def get_policy_version(self, policy_arn, version_id) -> PolicyVersionTypeDef:
        try:
            response: GetPolicyVersionResponseTypeDef = self.iam_client.get_policy_version(
                PolicyArn=policy_arn,
                VersionId=version_id
            )
            self.logger.debug(f"IAM Policy: {response}")
            return response.get('PolicyVersion', {})
        except ClientError as err:
            if err.response['Error']['Code'] == 'NoSuchEntityException':
                self.logger.error(str(err))
                return {'Error': str(err)}
            else:
                raise err

    def list_roles(self) -> list[RoleTypeDef]:
        try:
            response: ListRolesResponseTypeDef = self.iam_client.list_roles()
            roles = response.get('Roles', [])
            is_truncated = response.get('IsTruncated', False)
            marker = response.get('Marker')

            while is_truncated is True:
                self.logger.debug(f"Is truncated - marker: {marker})")
                response = self.iam_client.list_roles(
                    Marker=marker,
                )
                self.logger.info("Extending IAM Role List")
                roles.extend(response.get('Roles', []))
                is_truncated = response.get('IsTruncated')
                marker = response.get('Marker')

            self.logger.debug(f"Roles: {roles}")
            return roles
        except ClientError as err:
            self.logger.error(err)
            raise
