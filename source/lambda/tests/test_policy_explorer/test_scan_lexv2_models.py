#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_lexv2_models.type_defs import BotSummaryTypeDef, BotAliasSummaryTypeDef

from policy_explorer.policy_explorer_model import PolicyType
from policy_explorer.step_functions_lambda.scan_lex_v2_models_policy import Lexv2ModelsPolicy
from tests.test_policy_explorer.mock_data import event

logger = Logger(level='info', service="test_lex_v2")


@mock_aws
def test_mock_lexv2_models_scan_policy(mocker):
    # ARRANGE
    mock_lexv2(mocker)
    
    response = Lexv2ModelsPolicy(event).scan()
    logger.info(response)
    
    assert response == []


@mock_aws
def test_mock_lex_v2_scan_policy(mocker):
    
    list_bots_response: list[BotSummaryTypeDef] = [
        {
            'botId': '9OMNF4NCZH', 
            'botName': 'bot_with_resource_policy_with_org_dependency', 
            'botStatus': 'Available', 
            'botType': 'Bot'
            }, 
        {
            'botId': 'GVAIMLAYR6', 
            'botName': 'test-bot-for-aa', 
            'botStatus': 'Available', 
            'botType': 'Bot'
           },
       {
           'botId': '6D3L1KEIMW', 
           'botName': 'test_bot_with_no_resource_policy', 
           'botStatus': 'Available', 
           'botType': 'Bot'
        }
    ] 
    
    mock_lexv2(mocker,
               list_bots_response=list_bots_response,
               list_bot_aliases_response=[],
               describe_resource_policy_response=[])
    
    response = Lexv2ModelsPolicy(event=event).scan()
    logger.info(response)
    
    assert len(list(response)) == 4
    for resource in response:
        assert resource['PartitionKey'] == PolicyType.RESOURCE_BASED_POLICY.value
    

def mock_lexv2(mocker, list_bots_response=None, list_bot_aliases_response=None, describe_resource_policy_response=None):
    if list_bots_response is None:
        list_bots_response = []
    if list_bot_aliases_response is None:
        list_bot_aliases_response = []
    if describe_resource_policy_response is None:
        describe_resource_policy_response = []
        
    
    def mock_list_bots(self):
        return list_bots_response
    
    mocker.patch(
        "aws.services.lexv2.Lexv2Models.list_bots",
        mock_list_bots
    )
    
    def mock_list_bot_aliases(self, bot_id):
        list_bot_alias_response_9OMNF4NCZH: list[BotAliasSummaryTypeDef] = [
            {
                'botAliasId': 'TSTALIASID', 
                'botAliasName': 'TestBotAlias', 
                'description': 'test bot alias22', 
                'botVersion': 'DRAFT', 
                'botAliasStatus': 'Available'
                }
            ]     
        list_bot_alias_response_GVAIMLAYR6: list[BotAliasSummaryTypeDef] = [
            {
                'botAliasId': '61LUU51WEE', 
                'botAliasName': 'test-alias-2', 
                'botAliasStatus': 'Available', 
            }, 
            {
                'botAliasId': 'TSTALIASID', 
                'botAliasName': 'TestBotAlias', 
                'description': 'test bot alias2', 
                'botVersion': 'DRAFT', 
                'botAliasStatus': 'Available', 
            }
        ]
        list_bot_alias_response_6D3L1KEIMW: list[BotAliasSummaryTypeDef] = [
            {
                'botAliasId': 'CPD2HPZLO3',
                'botAliasName': 'botaliaswithnoresourcepolicy', 
                'botAliasStatus': 'Available'
            }, 
            {
                'botAliasId': 'TSTALIASID', 
                'botAliasName': 'TestBotAlias', 
                'description': 'test bot alias', 
                'botVersion': 'DRAFT', 
                'botAliasStatus': 'Available'
            }
        ]
        if bot_id == '9OMNF4NCZH':
            return list_bot_alias_response_9OMNF4NCZH
        elif bot_id == 'GVAIMLAYR6':
            return list_bot_alias_response_GVAIMLAYR6
        elif bot_id == '6D3L1KEIMW':
            return list_bot_alias_response_6D3L1KEIMW
        return []
    
    mocker.patch(
        "aws.services.lexv2.Lexv2Models.list_bot_aliases",
        mock_list_bot_aliases
    )
    
    def mock_describe_resource_policy(self, resource_arn: str):
        logger.info(f"configure these: {resource_arn}")
        if resource_arn == "arn:aws:lex:us-east-1:123456789012:bot/9OMNF4NCZH":
            return '{\"Version\":\"2012-10-17\",\"Id\":\"aasd\",\"Statement\":[{\"Sid\":\"11\",\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"lex:*\",\"Resource\":\"arn:aws:lex:us-east-1:123456789012:bot/9OMNF4NCZH\",\"Condition\":{\"StringEquals\":{\"aws:PrincipalOrgID\":\"o-eci09zojnh\"}}}]}'
        elif resource_arn == 'arn:aws:lex:us-east-1:123456789012:bot-alias/9OMNF4NCZH/TSTALIASID':
            return {'Error': 'There is no policy for resourceArn arn:aws:lex:us-east-1:123456789012:bot-alias/9OMNF4NCZH/TSTALIASID. Create a resource-based policy and try your request again.'}
        elif resource_arn == 'arn:aws:lex:us-east-1:123456789012:bot/GVAIMLAYR6':
            return '{\"Version\":\"2012-10-17\",\"Id\":\"aasd\",\"Statement\":[{\"Sid\":\"11\",\"Effect\":\"Allow\",\"Principal\":{\"AWS\":[\"arn:aws:iam::123456789012:root\",\"arn:aws:iam::123456789012:role/Admin\"]},\"Action\":\"lex:*\",\"Resource\":\"arn:aws:lex:us-east-1:123456789012:bot/GVAIMLAYR6\"}]}'
        elif resource_arn == 'arn:aws:lex:us-east-1:123456789012:bot-alias/GVAIMLAYR6/61LUU51WEE':
            return '{\"Version\":\"2012-10-17\",\"Id\":\"aasd\",\"Statement\":[{\"Sid\":\"11\",\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"arn:aws:iam::123456789012:root\"},\"Action\":\"lex:*\",\"Resource\":\"arn:aws:lex:us-east-1:123456789012:bot-alias/GVAIMLAYR6/61LUU51WEE\",\"Condition\":{\"StringEquals\":{\"aws:PrincipalOrgID\":\"o-eci09zojnh\"}}}]}'
        elif resource_arn == 'arn:aws:lex:us-east-1:123456789012:bot-alias/GVAIMLAYR6/TSTALIASID':
            return '{\"Version\":\"2012-10-17\",\"Id\":\"aasd\",\"Statement\":[{\"Sid\":\"11\",\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"arn:aws:iam::123456789012:root\"},\"Action\":\"lex:*\",\"Resource\":\"arn:aws:lex:us-east-1:123456789012:bot-alias/GVAIMLAYR6/TSTALIASID\"}]}'
        elif resource_arn == 'arn:aws:lex:us-east-1:123456789012:bot/6D3L1KEIMW':
            return {'Error': 'There is no policy for resourceArn arn:aws:lex:us-east-1:123456789012:bot/6D3L1KEIMW. Create a resource-based policy and try your request again.'}
        elif resource_arn == 'arn:aws:lex:us-east-1:123456789012:bot-alias/6D3L1KEIMW/CPD2HPZLO3':
            return {'Error': 'There is no policy for resourceArn arn:aws:lex:us-east-1:123456789012:bot-alias/6D3L1KEIMW/CPD2HPZLO3. Create a resource-based policy and try your request again.'}
        elif resource_arn == 'arn:aws:lex:us-east-1:123456789012:bot/-alias/6D3L1KEIMW/TSTALIASID':
            return {'Error': 'There is no policy for resourceArn arn:aws:lex:us-east-1:123456789012:bot-alias/6D3L1KEIMW/TSTALIASID. Create a resource-based policy and try your request again.'}
        else:
            return {'Error': 'There is no policy for resourceArn arn:aws:lex:us-east-1:123456789012:bot-alias/6D3L1KEIMW/TSTALIASID. Create a resource-based policy and try your request again.'}
    
    mocker.patch(
        "aws.services.lexv2.Lexv2Models.describe_resource_policy",
        mock_describe_resource_policy
    )