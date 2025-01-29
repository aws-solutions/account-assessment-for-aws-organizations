#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv

from aws.utils.exceptions import resource_not_found_exception_handler, service_exception_handler
from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws_lambda_powertools import Logger
from mypy_boto3_kms.type_defs import KeyListEntryTypeDef, GetKeyPolicyResponseTypeDef, ListKeysResponseTypeDef


class KeyManagementService:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('kms', credentials=account_credentials, region=region)
        self.kms_client = boto_session.get_client()

    @service_exception_handler
    def list_keys(self) -> list[KeyListEntryTypeDef]:
        response: ListKeysResponseTypeDef = self.kms_client.list_keys()
        keys = response.get('Keys', [])
        is_truncated = response.get('Truncated', False)
        marker = response.get('NextMarker')

        while is_truncated is True:
            self.logger.debug(f"Is truncated - marker: {marker})")
            response = self.kms_client.list_keys(
                Marker=marker
            )
            self.logger.info("Extending Key List")
            keys.extend(response.get('Keys', []))
            is_truncated = response.get('Truncated')
            marker = response.get('NextMarker')

        self.logger.debug(f"Keys: {keys}")
        return keys

    @resource_not_found_exception_handler
    def get_key_policy(self, key_id) -> GetKeyPolicyResponseTypeDef:
        response = self.kms_client.get_key_policy(
            KeyId=key_id,
            PolicyName='default'  # The only valid name is default
        )
        self.logger.debug(f"Key Policy: {response}")
        return response
