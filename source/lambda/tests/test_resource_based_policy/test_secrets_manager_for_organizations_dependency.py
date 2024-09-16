#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import datetime

from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_secretsmanager.type_defs import SecretListEntryTypeDef, GetResourcePolicyResponseTypeDef

from resource_based_policy.step_functions_lambda.scan_secrets_manager_policy import SecretsManagerPolicy
from tests.test_resource_based_policy.mock_data import event

logger = Logger(level="info", service="test_code_build")


@mock_aws
def test_mock_secretsmanager_scan_policy_no_policies(mocker):
    # ARRANGE
    mock_secretsmanager(mocker)

    # ARRANGE
    response = SecretsManagerPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_aws
def test_mock_secretsmanager_scan_policy(mocker):
    # ARRANGE
    list_secrets_response: list[SecretListEntryTypeDef] = [
        {
            "ARN": "mock:arn",
            "Name": "mock_name",
            "Description": "string",
            "KmsKeyId": "string",
            "RotationEnabled": True,
            "RotationLambdaARN": "string",
            "RotationRules": {
                "AutomaticallyAfterDays": 123,
                "Duration": "string",
                "ScheduleExpression": "string"
            },
            "LastRotatedDate": datetime.datetime.now(),
            "LastChangedDate": datetime.datetime.now(),
            "LastAccessedDate": datetime.datetime.now(),
            "DeletedDate": datetime.datetime.now(),
            "NextRotationDate": datetime.datetime.now(),
            "Tags": [
                {
                    "Key": "string",
                    "Value": "string"
                },
            ],
            "SecretVersionsToStages": {
                "string": [
                    "string",
                ]
            },
            "OwningService": "string",
            "CreatedDate": datetime.datetime.now(),
            "PrimaryRegion": "string"
        },
    ]

    get_resource_policy_response: GetResourcePolicyResponseTypeDef = {
        "ARN": "mock:arn",
        "Name": "mock_name",
        "ResourcePolicy": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":["
                          "\"secretsmanager:GetSecretValue\"],\"Resource\":\"*\",\"Condition\":{\"StringEquals\":{"
                          "\"aws:PrincipalOrgID\":\"o-a1b2c3d4e5\"}}}]}",
        "ResponseMetadata": {
            "RequestId": "request_id",
            "HostId": "host_id",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {"mock_key": "mock_value"},
            "RetryAttempts": 3,
        }
    }

    mock_secretsmanager(mocker,
                        list_secrets_response,
                        get_resource_policy_response)

    # ACT
    response = SecretsManagerPolicy(event).scan()
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


def mock_secretsmanager(mocker,
                        list_secrets_response=None,
                        get_resource_policy_response=None):

    # ARRANGE
    if list_secrets_response is None:
        list_secrets_response = []

    if get_resource_policy_response is None:
        get_resource_policy_response = []

    def mock_list_secrets(self):
        return list_secrets_response

    mocker.patch(
        "aws.services.secrets_manager.SecretsManager.list_secrets",
        mock_list_secrets
    )

    def mock_get_resource_policy(self, secret_id):
        return get_resource_policy_response

    mocker.patch(
        "aws.services.secrets_manager.SecretsManager.get_resource_policy",
        mock_get_resource_policy
    )
