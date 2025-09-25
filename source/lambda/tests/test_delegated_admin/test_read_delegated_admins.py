#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from mypy_boto3_dynamodb.service_resource import Table

from delegated_admins import read_delegated_admins
from delegated_admins.delegated_admins_repository import DelegatedAdminsRepository
from delegated_admins.read_delegated_admins import ReadDelegatedAdmins
from tests.test_utils.testdata_factory import TestLambdaContext
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
        result = read_delegated_admins.lambda_handler({}, TestLambdaContext())

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
        result = class_under_test.read_delegated_admins(APIGatewayProxyEvent({}), TestLambdaContext())

        # ASSERT
        assert created_items[0] in result['Results']
        assert created_items[1] in result['Results']
        assert created_items[2] in result['Results']

    def test_pagination_with_max_results(delegated_admin_table):
        # ARRANGE
        repository = DelegatedAdminsRepository()
        items = []
        for i in range(5):
            items.append(delegated_admin_create_request(f'service{i}.amazonaws.com', f'account-{i}'))
        created_items = repository.create_all(items)

        class_under_test = ReadDelegatedAdmins()

        event_data = {
            'queryStringParameters': {
                'maxResults': '2'
            }
        }
        result = class_under_test.read_delegated_admins(APIGatewayProxyEvent(event_data), TestLambdaContext())

        assert len(result['Results']) == 2
        assert 'Pagination' in result
        assert isinstance(result['Pagination']['hasMoreResults'], bool)

    def test_pagination_with_legacy_limit_parameter(delegated_admin_table):
        repository = DelegatedAdminsRepository()
        items = []
        for i in range(5):
            items.append(delegated_admin_create_request(f'service{i}.amazonaws.com', f'account-{i}'))
        created_items = repository.create_all(items)

        class_under_test = ReadDelegatedAdmins()

        event_data = {
            'queryStringParameters': {
                'limit': '3'
            }
        }
        result = class_under_test.read_delegated_admins(APIGatewayProxyEvent(event_data), TestLambdaContext())

        assert len(result['Results']) == 3
        assert 'Pagination' in result

    def test_pagination_parameter_priority(delegated_admin_table):
        # ARRANGE
        repository = DelegatedAdminsRepository()
        items = []
        for i in range(5):
            items.append(delegated_admin_create_request(f'service{i}.amazonaws.com', f'account-{i}'))
        created_items = repository.create_all(items)

        class_under_test = ReadDelegatedAdmins()

        event_data = {
            'queryStringParameters': {
                'limit': '4',
                'maxResults': '2'  # This should win
            }
        }
        result = class_under_test.read_delegated_admins(APIGatewayProxyEvent(event_data), TestLambdaContext())

        assert len(result['Results']) == 2  # Should use maxResults, not limit

    def test_pagination_response_structure(delegated_admin_table):
        repository = DelegatedAdminsRepository()
        created_items = repository.create_all(test_items)

        class_under_test = ReadDelegatedAdmins()

        event_data = {
            'queryStringParameters': {
                'maxResults': '2'
            }
        }
        result = class_under_test.read_delegated_admins(APIGatewayProxyEvent(event_data), TestLambdaContext())

        assert 'Results' in result
        assert 'Pagination' in result
        assert isinstance(result['Results'], list)
        assert isinstance(result['Pagination'], dict)
        assert 'hasMoreResults' in result['Pagination']
        assert isinstance(result['Pagination']['hasMoreResults'], bool)

    def test_backward_compatibility_no_pagination_params(delegated_admin_table):
        repository = DelegatedAdminsRepository()
        created_items = repository.create_all(test_items)

        class_under_test = ReadDelegatedAdmins()

        result = class_under_test.read_delegated_admins(APIGatewayProxyEvent({}), TestLambdaContext())

        assert len(result['Results']) == 3
        assert 'Pagination' in result
        assert result['Pagination']['hasMoreResults'] == False
        assert result['Pagination']['nextToken'] is None

    def test_pagination_with_empty_dict_event(delegated_admin_table):
        repository = DelegatedAdminsRepository()
        created_items = repository.create_all(test_items)

        class_under_test = ReadDelegatedAdmins()

        result = class_under_test.read_delegated_admins({}, {})

        assert len(result['Results']) == 3
        assert 'Pagination' in result