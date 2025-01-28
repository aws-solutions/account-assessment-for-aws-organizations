# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from os import getenv

from aws_lambda_powertools import Logger

from mypy_boto3_schemas.type_defs import ListRegistriesResponseTypeDef, GetResourcePolicyResponseTypeDef, RegistrySummaryTypeDef

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler

class EventBridgeSchemas:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        self.account_id = account_id
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f'Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}')
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session: Boto3Session = Boto3Session('schemas', credentials=account_credentials, region=region)
        self.schemas_client = boto_session.get_client()
        
    @service_exception_handler
    def list_registries(self) -> list[RegistrySummaryTypeDef]:
        response: ListRegistriesResponseTypeDef = self.schemas_client.list_registries(
            Scope='LOCAL'
        )
        
        registries_list = response.get('Registries', [])
        next_token = response.get('NextToken', None)
        
        while next_token is not None:
            self.logger.debug(f"Next Token Return: {next_token}")
            response = self.schemas_client.list_registries(
                NextToken=next_token,
                Scope='LOCAL'
            )
            self.logger.info(f"Extending Registries summary list")
            registries_list.extend(response.get('Registries', []))
            next_token = response.get('NextToken', None)
            
        return registries_list
    
    
    @resource_not_found_exception_handler
    def get_resource_policy(self, registry_name) -> str:
        response: GetResourcePolicyResponseTypeDef = self.schemas_client.get_resource_policy(
            RegistryName=registry_name
        )
        self.logger.debug(f"Resource Policy for {registry_name}: {response}")
        return response.get('Policy')