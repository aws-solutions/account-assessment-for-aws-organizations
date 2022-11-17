# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json

from aws_lambda_powertools.utilities.typing import LambdaContext

from resource_based_policy.supported_configuration import scan_configurations
from resource_based_policy.supported_configuration.scan_config_repository import ScanConfigRepository
from resource_based_policy.supported_configuration.supported_regions_and_services import SUPPORTED_REGIONS, \
    SUPPORTED_SERVICES
from tests.test_utils.testdata_factory import scan_config_create_request


def describe_read_scan_configs():
    item1 = scan_config_create_request([], 'config1')
    item2 = scan_config_create_request(['acc-id-1'], 'config2')
    item3 = scan_config_create_request(['acc-id-2', 'acc-id-3'], 'config3')
    test_items = [
        item1,
        item2,
        item3
    ]

    def test_that_it_returns_an_empty_list(resource_based_policies_table):
        # ARRANGE

        # ACT
        result = scan_configurations.lambda_handler({}, LambdaContext())

        # ASSERT
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['SavedConfigurations'] == []
        assert body['SupportedServices'] == SUPPORTED_SERVICES
        assert body['SupportedRegions'] == SUPPORTED_REGIONS

    def test_that_when_put_3_items_it_returns_all_items(resource_based_policies_table):
        # ARRANGE
        config1 = ScanConfigRepository().create_scan_config(item1)
        config2 = ScanConfigRepository().create_scan_config(item2)
        config3 = ScanConfigRepository().create_scan_config(item3)

        # ACT
        result = scan_configurations.lambda_handler({}, LambdaContext())

        # ASSERT
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        saved_configurations = body['SavedConfigurations']
        assert len(saved_configurations) == len(test_items)
        assert config1 in saved_configurations
        assert config2 in saved_configurations
        assert config3 in saved_configurations
