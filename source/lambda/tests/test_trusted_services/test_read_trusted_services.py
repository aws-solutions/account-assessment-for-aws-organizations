# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

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
