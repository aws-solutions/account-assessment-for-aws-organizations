# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_lexv2_models.type_defs import BotSummaryTypeDef, BotAliasSummaryTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.lexv2 import Lexv2Models, LexResource, LexResourceTypes
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from aws.utils.get_partition import partition_name_for_current_region
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn    

class Lexv2ModelsPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']
        self.lex_resources: list[LexResource] = []
        
    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)
    
    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning Lex v2 Models Policies in {region}")
        lexv2_client = Lexv2Models(self.account_id, region)
        self.lex_resources = self._get_lex_resources(lexv2_client=lexv2_client, region=region)
        lex_resource_names_and_policies: list[model.PolicyDetails] = self._get_lex_resources_and_policies(self.lex_resources, lexv2_client)
        lex_resource_dynamodb_items = []
        for lex_resource in lex_resource_names_and_policies:
            if lex_resource.get('Policy'):
                lex_resource_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(lex_resource))
        self.logger.debug(f"Lex Resources and policies {lex_resource_dynamodb_items}")
        return lex_resource_dynamodb_items
    
    def _get_lex_resources(self, lexv2_client: Lexv2Models, region: str) -> list[LexResource]:
        resources: list[LexResource] = []
        bots: list[BotSummaryTypeDef] = lexv2_client.list_bots()
        for bot in bots:
            resources.append(LexResource(
                Id=bot.get('botId'),
                Name=bot.get('botName'),
                Type=LexResourceTypes.BOT,
                Region=region,
                AccountId=self.account_id,
            ))
            self._get_lex_bot_aliases(bot_id=bot.get("botId"), resources=resources, lexv2_client=lexv2_client, region=region)
        return resources
        
    def _get_lex_bot_aliases(self, bot_id: str, resources: list[LexResource], lexv2_client: Lexv2Models, region: str) -> None:
        bot_aliases: list[BotAliasSummaryTypeDef] = lexv2_client.list_bot_aliases(bot_id)
        for bot_alias in bot_aliases:
                resources.append(LexResource(
                Id=f'{bot_id}/{bot_alias.get("botAliasId")}',
                Name=bot_alias.get('botAliasName'),
                Type=LexResourceTypes.BOT_ALIAS,
                Region=region,
                AccountId=self.account_id,
            ))
        return resources
             
    def _get_lex_resources_and_policies(self, lex_resources: list[LexResource], lexv2_client: Lexv2Models)-> list[model.PolicyDetails]:
        return list(self._get_lex_resource_policy(lex_resource=lex_resource, lexv2_client=lexv2_client) for lex_resource in lex_resources)
    
    @staticmethod
    def _get_lex_resource_policy(lex_resource: LexResource, lexv2_client: Lexv2Models) -> model.PolicyDetails:
        resource_arn: str = f"arn:{partition_name_for_current_region()}:lex:{lex_resource.get('Region')}:{lex_resource.get('AccountId')}:{lex_resource.get('Type').value}/{lex_resource.get('Id')}"
        policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
        resource_policy: str = lexv2_client.describe_resource_policy(resource_arn=resource_arn)
        policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
        policy_details.update({'Policy': resource_policy})
        return policy_details