# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import enum
from typing import TypedDict
from os import getenv

from aws_lambda_powertools import Logger

from mypy_boto3_lexv2_models.type_defs import ListBotsResponseTypeDef, ListBotAliasesResponseTypeDef
from mypy_boto3_lexv2_models.type_defs import BotSummaryTypeDef, BotAliasSummaryTypeDef, DescribeResourcePolicyResponseTypeDef

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler
from aws.utils.get_partition import partition_name_for_current_region

class LexResourceTypes(enum.Enum):
    BOT = 'bot'
    BOT_ALIAS = 'bot-alias'
    
class LexResource(TypedDict):
    Id: str
    Name: str
    Type: LexResourceTypes
    Region: str
    AccountId: str

class Lexv2Models:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        self.account_id = account_id
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f'Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}')
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session: Boto3Session = Boto3Session('lexv2-models', credentials=account_credentials, region=region)
        self.lexv2models_client = boto_session.get_client()
    
    @service_exception_handler
    def list_bots(self) -> list[BotSummaryTypeDef]:
        response: ListBotsResponseTypeDef = self.lexv2models_client.list_bots()

        bot_summary_list = response.get('botSummaries', [])
        next_token = response.get('nextToken', None)
        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token}") 
            response = self.lexv2models_client.list_bots(
                nextToken=next_token
            )
            self.logger.info(f"Extending Bots summary list")
            self.bot_summary_list.extend(response.get('botSummaries', []))
            next_token = response.get('nextToken', None) 
        return bot_summary_list
    
    @service_exception_handler
    def list_bot_aliases(self, bot_id: str) -> list[BotAliasSummaryTypeDef]:
        response: ListBotAliasesResponseTypeDef = self.lexv2models_client.list_bot_aliases(
            botId=bot_id
        )
    
        bot_aliases_summary_list = response.get('botAliasSummaries', [])
        
        next_token = response.get('nextToken', None)
        
        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token}") 
            response = self.lexv2models_client.list_bot_aliases(
                botId=bot_id,
                nextToken=next_token
            )
            self.logger.info(f"Extending Bot aliases summary list")
            bot_aliases_summary_list.extend(response.get('botAliasSummaries', []))
            next_token = response.get('nextToken', None) 
        
        return bot_aliases_summary_list
    
    @resource_not_found_exception_handler
    def describe_resource_policy(self, resource_arn: str) -> str:
        response: DescribeResourcePolicyResponseTypeDef = self.lexv2models_client.describe_resource_policy(
            resourceArn = resource_arn
        )
        self.logger.debug(f"Describe Resource Policy Response for {resource_arn}: {response}")
        return response.get("policy")
        