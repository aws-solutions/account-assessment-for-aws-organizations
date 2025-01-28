# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from resource_based_policy.read_resource_based_policies import ReadResourceBasedPolicies
from resource_based_policy.resource_based_policies_repository import ResourceBasedPoliciesRepository
from tests.test_utils.testdata_factory import resource_based_policies_create_request


def describe_read_resource_based_policies():
    item1 = resource_based_policies_create_request('config')
    item2 = resource_based_policies_create_request('ram')

    test_items = [
        item1,
        item2
    ]

    def test_that_it_returns_an_empty_list(resource_based_policies_table, job_history_table):
        # ARRANGE
        function_under_test = ReadResourceBasedPolicies()

        # ACT
        result = function_under_test.read_resource_based_policies({}, {})

        # ASSERT
        assert len(result['Results']) == 0

    def test_that_when_put_2_items_it_returns_all_items(resource_based_policies_table, job_history_table):
        # ARRANGE
        repository = ResourceBasedPoliciesRepository()
        resource_based_policies = repository.create_all(test_items)

        class_under_test = ReadResourceBasedPolicies()

        # ACT
        result = class_under_test.read_resource_based_policies({}, {})

        # ASSERT
        assert len(result['Results']) == len(resource_based_policies)
        assert resource_based_policies[0] in result['Results']
        assert resource_based_policies[1] in result['Results']
