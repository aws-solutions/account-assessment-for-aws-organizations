#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_ram.type_defs import ResourceTypeDef

from policy_explorer.policy_explorer_model import PolicyType
from policy_explorer.step_functions_lambda.scan_ram_policy import RAMPolicy
from tests.test_policy_explorer.mock_data import event

logger = Logger(level="info")


@mock_aws
def test_mock_ram_scan_policy_no_policies(mocker):
    # ARRANGE
    mock_ram(mocker)

    # ACT
    response = RAMPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_aws
def test_mock_ram_scan_policy(mocker):
    # Arrange
    list_resources_response: list[ResourceTypeDef] = [
        {"arn": "arn:aws:ram:*:111122223333:resource-share/myresource"}
    ]

    mock_ram(
        mocker,
        list_resources_response=list_resources_response,
        get_resource_policy_response=[],
    )

    # Act
    response = RAMPolicy(event).scan()
    logger.info(f"Response: {response}")

    # Assert
    assert len(list(response)) == 2
    for resource in response:
        assert resource.get('PartitionKey') == PolicyType.RESOURCE_BASED_POLICY.value


def mock_ram(mocker, list_resources_response=None, get_resource_policy_response=None):
    # Arrange
    if not list_resources_response:
        list_resources_response = []

    if not get_resource_policy_response:
        get_resource_policy_response = []

    def mock_list_resources(self):
        return list_resources_response

    mocker.patch("aws.services.ram.RAM.list_resources", mock_list_resources)

    def mock_get_resource_policy(self, resource_arn: str):
        if resource_arn == "arn:aws:ram:*:111122223333:resource-share/myresource":
            return '{"Version":"2012-10-17","Statement":[{"Action":["ram:*"], "Effect":"Allow","Resource":"*", "Condition":{"StringEquals":{"aws:PrincipalOrgID":"o-abcdefghij"}}}]}'

        else:
            return {"Error": "There is no policy found for this resource."}

    mocker.patch(
        "aws.services.ram.RAM.get_resource_policy", mock_get_resource_policy
    )
