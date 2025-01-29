#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv

from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws_lambda_powertools import Logger
from mypy_boto3_secretsmanager.type_defs import ListSecretsResponseTypeDef, SecretListEntryTypeDef, \
    GetResourcePolicyResponseTypeDef


class SecretsManager:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('secretsmanager', credentials=account_credentials, region=region)
        self.secrets_manager_client = boto_session.get_client()

    @service_exception_handler
    def list_secrets(self) -> list[SecretListEntryTypeDef]:
        response: ListSecretsResponseTypeDef = self.secrets_manager_client.list_secrets(
            SortOrder='asc'
        )

        secrets_data = response.get('SecretList', [])
        next_token = response.get('NextToken', None)

        while next_token is not None:
            self.logger.debug(f"NextToken Returned: {next_token})")
            response = self.secrets_manager_client.list_secrets(
                SortOrder='asc',
                NextToken=next_token
            )
            self.logger.info("Extending Secrets List")
            secrets_data.extend(response.get('SecretList', []))
            next_token = response.get('NextToken', None)

        return secrets_data

    @resource_not_found_exception_handler
    def get_resource_policy(self, secret_id) -> GetResourcePolicyResponseTypeDef:
        response = self.secrets_manager_client.get_resource_policy(
            SecretId=secret_id
        )
        self.logger.debug(f"Policy attached to the secret: {response}")
        return response

