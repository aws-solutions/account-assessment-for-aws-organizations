# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_dynamodb.service_resource import Table

from delegated_admins import read_delegated_admins
from delegated_admins.delegated_admins_repository import DelegatedAdminsRepository
from delegated_admins.read_delegated_admins import ReadDelegatedAdmins
from tests.test_utils.testdata_factory import delegated_admin_create_request


def describe_read_delegated_admins():
    item1 = delegated_admin_create_request('ssm.amazonaws.com', 'dev-account-id')
    item2 = delegated_admin_create_request('guardduty.amazonaws.com', 'dev-account-id')
    item3 = delegated_admin_create_request('guardduty.amazonaws.com', 'dev-2-account-id')
    test_items = [
        item1,
        item2,
        item3
    ]

    def test_that_it_returns_an_empty_list(delegated_admin_table: Table):
        # ARRANGE

        # ACT
        result = read_delegated_admins.lambda_handler({}, LambdaContext())

        # ASSERT
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['Results'] == []

    def test_that_when_put_3_items_it_returns_all_items(delegated_admin_table):
        # ARRANGE
        repository = DelegatedAdminsRepository()
        created_items = repository.create_all(test_items)

        class_under_test = ReadDelegatedAdmins()

        # ACT
        result = class_under_test.read_delegated_admins(APIGatewayProxyEvent({}), LambdaContext())

        # ASSERT
        assert created_items[0] in result['Results']
        assert created_items[1] in result['Results']
        assert created_items[2] in result['Results']
