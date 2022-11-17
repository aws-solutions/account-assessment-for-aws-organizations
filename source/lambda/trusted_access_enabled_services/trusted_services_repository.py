# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
from logging import Logger
from typing import List

from aws.services.dynamodb import DynamoDB
from trusted_access_enabled_services.trusted_access_model import TrustedAccessModel, TrustedAccessCreateRequest
from utils.base_repository import BaseRepository

PARTITION_KEY_TRUSTED_SERVICES = 'trusted-services'


def sort_key_trusted_services(service_principal: str):
    return service_principal


class TrustedServicesRepository(BaseRepository[TrustedAccessModel]):
    def __init__(self):
        super().__init__()
        self.logger = Logger(os.getenv('LOG_LEVEL'))
        self.table = DynamoDB(os.getenv('COMPONENT_TABLE'))

    def find_all_trusted_services(self) -> List[TrustedAccessModel]:
        return self.table.find_items_by_partition_key(PARTITION_KEY_TRUSTED_SERVICES)

    def create_all(self, requests: List[TrustedAccessCreateRequest]) -> List[TrustedAccessModel]:
        trusted_services: List[TrustedAccessModel] = list(
            self._map_to_model(request)
            for request in requests
        )
        self.table.put_items(trusted_services)
        return trusted_services

    def create_trusted_service(self, request: TrustedAccessCreateRequest) -> TrustedAccessModel:
        trusted_service = self._map_to_model(request)
        self.table.put_item(trusted_service)
        return trusted_service

    def get_trusted_service(self, service_principal) -> TrustedAccessModel:
        return self.table.get_by_id(
            PARTITION_KEY_TRUSTED_SERVICES,
            sort_key_trusted_services(service_principal)
        )

    def _map_to_model(self, request: TrustedAccessCreateRequest) -> TrustedAccessModel:
        return dict(request,
                    PartitionKey=PARTITION_KEY_TRUSTED_SERVICES,
                    SortKey=sort_key_trusted_services(request['ServicePrincipal']),
                    ExpiresAt=self._calculate_expires_at()
                    )
