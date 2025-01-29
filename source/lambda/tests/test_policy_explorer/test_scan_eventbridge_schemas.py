#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_schemas.type_defs import RegistrySummaryTypeDef

from policy_explorer.policy_explorer_model import PolicyType
from policy_explorer.step_functions_lambda.scan_eventbridge_schemas_policy import EventBridgeSchemasPolicy
from tests.test_policy_explorer.mock_data import event

logger = Logger(level="info")


@mock_aws
def test_no_schema(mocker):
    # ARRANGE
    mock_eventbridge_schemas(mocker)
    
    # ACT
    response = EventBridgeSchemasPolicy(event).scan()
    logger.info(response)
    
    # ASSERT
    assert len(list(response)) == 0
    for resource in response:
        assert resource.get("PartitionKey") == PolicyType.RESOURCE_BASED_POLICY.value


@mock_aws
def test_mock_schemas(mocker):
    list_registries_response:list[RegistrySummaryTypeDef] = [
        {
            'RegistryArn': 'arn:aws:schemas:us-west-2:111111111111:registry/default', 
            'RegistryName': 'default', 
            'Tags': {
                
            }
        }
    ]
    
    mock_eventbridge_schemas(mocker,
                             list_registries_response=list_registries_response,
                             get_resource_policy_response=[])
    
    response = EventBridgeSchemasPolicy(event=event).scan()
    logger.info(response)
    
    assert len(list(response)) == 2
    
def mock_eventbridge_schemas(mocker,
                             list_registries_response=None,
                             get_resource_policy_response=None):
    if list_registries_response is None:
        list_registries_response = []
    if get_resource_policy_response is None:
        get_resource_policy_response = []

    def mock_list_registries(self):
        return list_registries_response
    
    mocker.patch(
        "aws.services.eventbridge_schemas.EventBridgeSchemas.list_registries",
        mock_list_registries
    )
    
    def mock_get_resource_policy(self, registry_name):
        if (registry_name == 'default'):
            return '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"AllowUserRestoreFromSnapshot\",\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"arn:aws:iam::111111111111:root\"},\"Action\":\"schemas:ListRegistries\",\"Resource\":\"arn:aws:schemas:us-west-2:111111111111:schema/default/test-for-aa\",\"Condition\":{\"StringEqual\":{\"aws:PrincipalOrgID\":\"o-eci09zojnh\"}}}]}'
        else:
            return {'Error': 'There is no policy for registry default. Create a resource-based policy and try your request again.'}
    mocker.patch(
        "aws.services.eventbridge_schemas.EventBridgeSchemas.get_resource_policy",
        mock_get_resource_policy
    )