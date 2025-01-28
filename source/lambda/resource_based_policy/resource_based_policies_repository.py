# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
from logging import Logger
from typing import List

from aws.services.dynamodb import DynamoDB
from resource_based_policy.resource_based_policy_model import ResourceBasedPolicyDBModel, \
    ResourceBasedPolicyResponseModel
from utils.base_repository import BaseRepository

PARTITION_KEY_POLICIES = 'Policies'


def sort_key_resource_based_policies(
        service_name: str,
        account_id: str,
        region: str,
        resource_name: str,
        dependency_type: str):
    return f"{service_name}#{account_id}#{region}#{resource_name}#{dependency_type}"


class ResourceBasedPoliciesRepository(BaseRepository[ResourceBasedPolicyResponseModel]):
    def __init__(self):
        super().__init__()
        self.logger = Logger(os.getenv('LOG_LEVEL'))
        self.table = DynamoDB(os.getenv('COMPONENT_TABLE'))

    def find_all_policies(self) -> List[ResourceBasedPolicyDBModel]:
        return self.table.find_items_by_partition_key(PARTITION_KEY_POLICIES)

    def create_all(self, requests: List[ResourceBasedPolicyResponseModel]) -> List[ResourceBasedPolicyDBModel]:
        policies: List[ResourceBasedPolicyDBModel] = list(
            self._map_to_model(request)
            for request in requests
        )
        self.table.put_items(policies)
        return policies

    def create_policy(self, request: ResourceBasedPolicyResponseModel) -> ResourceBasedPolicyDBModel:
        policy = self._map_to_model(request)
        self.table.put_item(policy)
        return policy

    def get_policy(self, service_name: str, account_id: str, region: str, resource_name: str, dependency_type: str) \
            -> ResourceBasedPolicyDBModel:
        return self.table.get_by_id(
            PARTITION_KEY_POLICIES,
            sort_key_resource_based_policies(service_name, account_id, region, resource_name, dependency_type)
        )

    def _map_to_model(self, request: ResourceBasedPolicyResponseModel) -> ResourceBasedPolicyDBModel:
        return ResourceBasedPolicyDBModel(
            request,
            PartitionKey=PARTITION_KEY_POLICIES,
            SortKey=sort_key_resource_based_policies(
                request['ServiceName'],
                request['AccountId'],
                request['Region'],
                request['ResourceName'],
                request['DependencyType']
            ),
            ExpiresAt=self._calculate_expires_at()
        )
        

