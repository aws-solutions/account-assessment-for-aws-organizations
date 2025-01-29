#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_config.type_defs import OrganizationConfigRuleTypeDef, \
    GetCustomRulePolicyResponseTypeDef

from policy_explorer.policy_explorer_model import PolicyType
from policy_explorer.step_functions_lambda.scan_config_rule_policy import ConfigRulePolicy
from tests.test_policy_explorer.mock_data import event

logger = Logger(level="info", service="test_code_build")


@mock_aws
def test_mock_config_scan_policy_no_policies(mocker):
    # ARRANGE
    mock_config(mocker)

    # ARRANGE
    response = ConfigRulePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_aws
def test_mock_config_scan_policy(mocker):
    # ARRANGE
    describe_organization_config_rules_response: list[OrganizationConfigRuleTypeDef] = [
        {
            'OrganizationConfigRuleName': 'ec2-no-amazon-key-pair',
            'OrganizationConfigRuleArn': '"arn:aws:config:us-west-2:111111111111:organization-config-rule/ec2-no-amazon-key-pair-yvylwqkv',
            'OrganizationManagedRuleMetadata': {
                'RuleIdentifier': 'EC2_NO_AMAZON_KEY_PAIR',
                'MaximumExecutionFrequency': 'TwentyFour_Hours'
            },
            'LastUpdateTime': "2023-11-22T14:21:09.607000-05:00"
        },
    ]

    get_organization_custom_rule_policy_response: GetCustomRulePolicyResponseTypeDef = {
        'PolicyText': "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":\"*\","
                      "\"Action\":[\"config:PutConfigRule\",\"config:DeleteConfigRule\"],"
                      "\"Resource\":\"arn:aws:config:*:*:config-rule/aws-service-rule/config-conforms.amazonaws.com"
                      "*\",\"Condition\":{\"StringEquals\":{\"aws:PrincipalOrgID\":\"o-abcd1234\"}}}]}",
        "ResponseMetadata": {
            "RequestId": "request_id",
            "HostId": "host_id",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {"mock_key": "mock_value"},
            "RetryAttempts": 3,
        }
    }

    mock_config(mocker,
             describe_organization_config_rules_response,
             get_organization_custom_rule_policy_response)

    # ACT
    response = ConfigRulePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 2
    for resource in response:
       assert resource.get("PartitionKey") == PolicyType.RESOURCE_BASED_POLICY.value


def mock_config(mocker,
                describe_organization_config_rules_response=None,
                get_organization_custom_rule_policy_response=None):

    # ARRANGE
    if describe_organization_config_rules_response is None:
        describe_organization_config_rules_response = []

    if get_organization_custom_rule_policy_response is None:
        get_organization_custom_rule_policy_response = []

    def mock_describe_organization_config_rules(self):
        return describe_organization_config_rules_response

    mocker.patch(
        "aws.services.config.Config.describe_organization_config_rules",
        mock_describe_organization_config_rules
    )

    def mock_get_organization_custom_rule_policy(self, organization_config_rule_name):
        return get_organization_custom_rule_policy_response

    mocker.patch(
        "aws.services.config.Config.get_organization_custom_rule_policy",
        mock_get_organization_custom_rule_policy
    )
