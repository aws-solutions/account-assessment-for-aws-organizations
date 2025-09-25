#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger

from tests.test_utils.testdata_factory import trusted_access_create_request
from trusted_access_enabled_services.read_trusted_services import ReadTrustedServices
from trusted_access_enabled_services.trusted_services_repository import TrustedServicesRepository


def describe_read_trusted_services():
    logger = Logger(level="info")

    item1 = trusted_access_create_request('config.amazonaws.com')
    item2 = trusted_access_create_request('ram.amazonaws.com')

    test_items = [
        item1,
        item2
    ]

    def test_that_it_returns_an_empty_list(trusted_services_table):
        # ARRANGE
        function_under_test = ReadTrustedServices()

        # ACT
        result = function_under_test.read_trusted_access_enabled_services({}, {})

        # ASSERT
        assert len(result['Results']) == 0

    def test_that_when_put_2_items_it_returns_all_items(trusted_services_table):
        # ARRANGE
        repository = TrustedServicesRepository()
        trusted_services = repository.create_all(test_items)

        class_under_test = ReadTrustedServices()

        # ACT
        result = class_under_test.read_trusted_access_enabled_services({}, {})

        # ASSERT
        assert len(result['Results']) == len(trusted_services)
        assert trusted_services[0] in result['Results']
        assert trusted_services[1] in result['Results']

    def test_pagination_with_max_results(trusted_services_table):
        # ARRANGE
        repository = TrustedServicesRepository()
        items = []
        for i in range(5):
            items.append(trusted_access_create_request(f'service{i}.amazonaws.com'))
        created_items = repository.create_all(items)

        class_under_test = ReadTrustedServices()

        # ACT - Test with maxResults parameter
        event_data = {
            'queryStringParameters': {
                'maxResults': '2'
            }
        }
        from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
        result = class_under_test.read_trusted_access_enabled_services(APIGatewayProxyEvent(event_data), {})

        # ASSERT
        assert len(result['Results']) == 2
        assert 'Pagination' in result
        assert isinstance(result['Pagination']['hasMoreResults'], bool)

    def test_pagination_with_legacy_limit_parameter(trusted_services_table):
        # ARRANGE
        repository = TrustedServicesRepository()
        items = []
        for i in range(5):
            items.append(trusted_access_create_request(f'service{i}.amazonaws.com'))
        created_items = repository.create_all(items)

        class_under_test = ReadTrustedServices()

        # ACT - Test with legacy limit parameter
        event_data = {
            'queryStringParameters': {
                'limit': '3'
            }
        }
        from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
        result = class_under_test.read_trusted_access_enabled_services(APIGatewayProxyEvent(event_data), {})

        # ASSERT
        assert len(result['Results']) == 3
        assert 'Pagination' in result

    def test_pagination_parameter_priority(trusted_services_table):
        # ARRANGE
        repository = TrustedServicesRepository()
        items = []
        for i in range(5):
            items.append(trusted_access_create_request(f'service{i}.amazonaws.com'))
        created_items = repository.create_all(items)

        class_under_test = ReadTrustedServices()

        # ACT - maxResults should take priority over limit
        event_data = {
            'queryStringParameters': {
                'limit': '4',
                'maxResults': '2'  # This should win
            }
        }
        from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
        result = class_under_test.read_trusted_access_enabled_services(APIGatewayProxyEvent(event_data), {})

        # ASSERT
        assert len(result['Results']) == 2  # Should use maxResults, not limit

    def test_pagination_response_structure(trusted_services_table):
        # ARRANGE
        repository = TrustedServicesRepository()
        trusted_services = repository.create_all(test_items)

        class_under_test = ReadTrustedServices()

        # ACT
        event_data = {
            'queryStringParameters': {
                'maxResults': '1'
            }
        }
        from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
        result = class_under_test.read_trusted_access_enabled_services(APIGatewayProxyEvent(event_data), {})

        # ASSERT - Verify response structure
        assert 'Results' in result
        assert 'Pagination' in result
        assert isinstance(result['Results'], list)
        assert isinstance(result['Pagination'], dict)
        assert 'hasMoreResults' in result['Pagination']
        assert isinstance(result['Pagination']['hasMoreResults'], bool)

    def test_backward_compatibility_no_pagination_params(trusted_services_table):
        # ARRANGE
        repository = TrustedServicesRepository()
        trusted_services = repository.create_all(test_items)

        class_under_test = ReadTrustedServices()

        # ACT - No pagination parameters
        from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
        result = class_under_test.read_trusted_access_enabled_services(APIGatewayProxyEvent({}), {})

        # ASSERT - Should return all results with pagination structure
        assert len(result['Results']) == 2
        assert 'Pagination' in result
        assert result['Pagination']['hasMoreResults'] == False
        assert result['Pagination']['nextToken'] is None

    def test_pagination_with_empty_dict_event(trusted_services_table):
        # ARRANGE
        repository = TrustedServicesRepository()
        trusted_services = repository.create_all(test_items)

        class_under_test = ReadTrustedServices()

        # ACT - Empty dict (like original tests)
        result = class_under_test.read_trusted_access_enabled_services({}, {})

        # ASSERT
        assert len(result['Results']) == 2
        assert 'Pagination' in result
