#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from os import getenv

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError
from mypy_boto3_sts import STSClient
from mypy_boto3_sts.type_defs import CredentialsTypeDef, AssumeRoleResponseTypeDef, GetCallerIdentityResponseTypeDef

from aws.utils.boto3_session import Boto3Session
from aws.utils.get_partition import partition_name_for_current_region


class SecurityTokenService:
    def __init__(self, **kwargs):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        kwargs.update({'region': self.get_sts_region})
        kwargs.update({'endpoint_url': self.get_sts_endpoint()})
        boto_session = Boto3Session('sts', **kwargs)
        self.sts_client: STSClient = boto_session.get_client()

    @property
    def get_sts_region(self):
        return getenv('AWS_REGION')

    @staticmethod
    def get_sts_endpoint():
        return "https://sts.%s.amazonaws.com" % getenv('AWS_REGION')

    def assume_role_by_name(
            self,
            account_id: str,
            role_name: str,
            partition: str = partition_name_for_current_region(),
            session_name: str = "account-assessment-session",
            duration: int = 900
    ) -> CredentialsTypeDef:
        try:
            role_arn = f"arn:{partition}:iam::{account_id}:role/{role_name}"
            credentials = self.assume_role_by_arn(role_arn, session_name, duration)
            return credentials
        except ClientError as e:
            logger = Logger(getenv('LOG_LEVEL'))
            logger.error(e)
            raise

    def assume_role_by_arn(self, role_arn: str, session_name: str, duration: int = 900) -> CredentialsTypeDef:
        try:
            response: AssumeRoleResponseTypeDef = self.sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=session_name,
                DurationSeconds=duration
            )
            return response['Credentials']
        except ClientError as err:
            self.logger.error(err)
            raise

    def get_caller_identity(self) -> GetCallerIdentityResponseTypeDef:
        try:
            response = self.sts_client.get_caller_identity()
            return response
        except ClientError as err:
            self.logger.error(err)
            raise
