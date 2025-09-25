#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os
from logging import Logger
from typing import List, Tuple

from aws.services.dynamodb import DynamoDB
from delegated_admins.delegated_admin_model import DelegatedAdminModel, DelegatedAdminCreateRequest
from utils.base_repository import BaseRepository
from utils.pagination_model import PaginationMetadata, DdbPagination
from utils.pagination_helper import build_pagination_metadata

PARTITION_KEY_DELEGATED_ADMINS = 'delegated-admins'


def sort_key_delegated_admins(service_principal: str, account_id: str):
    return service_principal + '#' + account_id


class DelegatedAdminsRepository(BaseRepository[DelegatedAdminModel]):
    def __init__(self):
        super().__init__()
        self.logger = Logger(os.getenv('LOG_LEVEL'))
        self.table = DynamoDB(os.getenv('COMPONENT_TABLE'))

    def find_all_delegated_admins(self) -> List[DelegatedAdminModel]:
        return self.table.find_items_by_partition_key(PARTITION_KEY_DELEGATED_ADMINS)

    def find_all_delegated_admins_paginated(self, pagination: DdbPagination) -> Tuple[List[DelegatedAdminModel], PaginationMetadata]:
        try:
            query_result = self.table.find_items_by_partition_key_paginated(PARTITION_KEY_DELEGATED_ADMINS, pagination)
            
            items = query_result.get('Items', [])
            last_evaluated_key = query_result.get('LastEvaluatedKey')
            
            pagination_metadata = build_pagination_metadata(last_evaluated_key)
            
            return items, pagination_metadata
            
        except Exception as error:
            self.logger.error(f"Error querying delegated admins: {error}")
            raise error

    def create_all(self, requests: List[DelegatedAdminCreateRequest]) -> List[DelegatedAdminModel]:
        delegated_admins: List[DelegatedAdminModel] = list(
            self._map_to_model(request)
            for request in requests
        )
        self.table.put_items(delegated_admins)
        return delegated_admins

    def create_trusted_service(self, request: DelegatedAdminCreateRequest) -> DelegatedAdminModel:
        delegated_admin = self._map_to_model(request)
        self.table.put_item(delegated_admin)
        return delegated_admin

    def get_delegated_admin(self, service_principal: str, account_id: str) -> DelegatedAdminModel:
        return self.table.get_by_id(
            PARTITION_KEY_DELEGATED_ADMINS,
            sort_key_delegated_admins(service_principal, account_id)
        )

    def _map_to_model(self, request: DelegatedAdminCreateRequest) -> DelegatedAdminModel:
        return dict(request,
                    PartitionKey=PARTITION_KEY_DELEGATED_ADMINS,
                    SortKey=sort_key_delegated_admins(request['ServicePrincipal'], request['AccountId']),
                    ExpiresAt=self._calculate_expires_at()
                    )
