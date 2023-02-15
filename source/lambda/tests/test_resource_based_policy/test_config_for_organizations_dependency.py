# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import datetime

from aws_lambda_powertools import Logger
from moto import mock_sts
from mypy_boto3_config.type_defs import OrganizationConfigRuleTypeDef, \
    GetCustomRulePolicyResponseTypeDef

from resource_based_policy.step_functions_lambda.scan_config_rule_policy import ConfigRulePolicy
from tests.test_resource_based_policy.mock_data import event

logger = Logger(level="info", service="test_code_build")


@mock_sts
def test_mock_config_scan_policy_no_policies(mocker):
    # ARRANGE
    mock_config(mocker)

    # ARRANGE
    response = ConfigRulePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_sts
def test_mock_config_scan_policy(mocker):
    # ARRANGE
    describe_organization_config_rules_response: list[OrganizationConfigRuleTypeDef] = [
        {
            'OrganizationConfigRuleName': 'mock_rule_name',
            'OrganizationConfigRuleArn': 'arn:mock_rule_name',
            'OrganizationManagedRuleMetadata': {
                'Description': 'string',
                'RuleIdentifier': 'string',
                'InputParameters': 'string',
                'MaximumExecutionFrequency': 'TwentyFour_Hours',
                'ResourceTypesScope': [
                    'string',
                ],
                'ResourceIdScope': 'string',
                'TagKeyScope': 'string',
                'TagValueScope': 'string'
            },
            'OrganizationCustomRuleMetadata': {
                'Description': 'string',
                'LambdaFunctionArn': 'string',
                'OrganizationConfigRuleTriggerTypes': [
                    'ConfigurationItemChangeNotification',
                ],
                'InputParameters': 'string',
                'MaximumExecutionFrequency': 'TwentyFour_Hours',
                'ResourceTypesScope': [
                    'string',
                ],
                'ResourceIdScope': 'string',
                'TagKeyScope': 'string',
                'TagValueScope': 'string'
            },
            'ExcludedAccounts': [
                'string',
            ],
            'LastUpdateTime': datetime.datetime.now,
            'OrganizationCustomPolicyRuleMetadata': {
                'Description': 'string',
                'OrganizationConfigRuleTriggerTypes': [
                    'ConfigurationItemChangeNotification',
                ],
                'InputParameters': 'string',
                'MaximumExecutionFrequency': 'TwentyFour_Hours',
                'ResourceTypesScope': [
                    'string',
                ],
                'ResourceIdScope': 'string',
                'TagKeyScope': 'string',
                'TagValueScope': 'string',
                'PolicyRuntime': 'string',
                'DebugLogDeliveryAccounts': [
                    'string',
                ]
            }
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
        assert resource["DependencyType"] in [
            "aws:PrincipalOrgID",
            "aws:PrincipalOrgPaths",
            "aws:ResourceOrgID",
            "aws:ResourceOrgPaths"
        ]


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
