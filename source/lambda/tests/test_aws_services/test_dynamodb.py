#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os
import uuid

from mypy_boto3_dynamodb.service_resource import Table

from aws.services.dynamodb import DynamoDB
from delegated_admins.delegated_admin_model import DelegatedAdminModel
from delegated_admins.delegated_admins_repository import PARTITION_KEY_DELEGATED_ADMINS, sort_key_delegated_admins
from tests.test_utils.testdata_factory import delegated_admin_create_request


def describe_put_items():
    create_request = delegated_admin_create_request('ssm.amazonaws.com', 'dev-account-id')
    delegated_admin_for_ssm: DelegatedAdminModel = dict(
        create_request,
        PartitionKey=PARTITION_KEY_DELEGATED_ADMINS,
        SortKey=sort_key_delegated_admins(create_request['ServicePrincipal'], create_request['AccountId'])
    )

    def test_write_delegated_admins(delegated_admin_table: Table):
        # ARRANGE
        ddb = DynamoDB(os.getenv("COMPONENT_TABLE"))

        # ACT
        ddb.put_items([
            delegated_admin_for_ssm,
        ])

        # ASSERT
        items = ddb.find_items_by_partition_key(PARTITION_KEY_DELEGATED_ADMINS)

        assert len(items) == 1
        for item in items:
            assert item.get('ServicePrincipal') == delegated_admin_for_ssm['ServicePrincipal']


    def test_write_multiple_batches(delegated_admin_table: Table):
        # ARRANGE
        ddb = DynamoDB(os.getenv("COMPONENT_TABLE"))

        number_of_items = 55  # arbitrary number greater than write batch size
        many_unique_items = []
        for _ in range(0, number_of_items):
            many_unique_items.append({
                **delegated_admin_for_ssm,
                'SortKey': sort_key_delegated_admins(delegated_admin_for_ssm['ServicePrincipal'], uuid.uuid4().hex)
            })

        # ACT
        ddb.put_items(many_unique_items)

        # ASSERT
        all_items = ddb.find_all()
        assert len(all_items) == number_of_items
