# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
from logging import Logger
from typing import List

from aws.services.dynamodb import DynamoDB
from resource_based_policy.supported_configuration.scan_configuration_model import ScanConfigModel, \
    ScanConfigCreateRequest
from utils.base_repository import BaseRepository

PARTITION_KEY_SCAN_CONFIGS = 'ScanConfigurations'


def sort_key_scan_config(configuration_name: str):
    return configuration_name


class ScanConfigRepository(BaseRepository):
    def __init__(self):
        super().__init__()
        self.logger = Logger(os.getenv('LOG_LEVEL'))
        self.dynamodb_resource_based_policies = DynamoDB(os.getenv('COMPONENT_TABLE'))

    def find_all_scan_configs(self) -> List[ScanConfigModel]:
        return self.dynamodb_resource_based_policies.find_items_by_partition_key(PARTITION_KEY_SCAN_CONFIGS)

    def create_scan_config(self, request: ScanConfigCreateRequest) -> ScanConfigModel:
        scan_config = self._map_to_model(request)
        self.dynamodb_resource_based_policies.put_item(scan_config)
        return scan_config

    def _map_to_model(self, request: ScanConfigCreateRequest) -> ScanConfigModel:
        return dict(request,
                    PartitionKey=PARTITION_KEY_SCAN_CONFIGS,
                    SortKey=sort_key_scan_config(request['ConfigurationName']),
                    ExpiresAt=self._calculate_expires_at()
                    )
