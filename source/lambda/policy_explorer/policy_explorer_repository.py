#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os
from logging import Logger
from typing import List

from botocore.exceptions import ClientError

from aws.services.dynamodb import DynamoDB
from policy_explorer.policy_explorer_model import DynamoDBPolicyItem, PolicyFilters, PolicyItem, DdbPagination, PaginationMetadata


class PoliciesRepository:
    def __init__(self):
        self.logger = Logger(os.getenv('LOG_LEVEL'))
        self.table = DynamoDB(os.getenv('COMPONENT_TABLE'))

    def create_all(self, requests: List[DynamoDBPolicyItem]):
        try:
            self.table.put_items(requests)
            return requests
        except ClientError as error:
            self.logger.error(error)
            raise error

    def find_all_by_policy_type(self, policy_type: str, region: str, filters: PolicyFilters,
                                pagination: DdbPagination) -> tuple[List[PolicyItem], PaginationMetadata]:
        try:
            query_result = self.table.query_paginated(policy_type, region, filters, pagination)
            
            items = query_result.get('Items', [])
            last_evaluated_key = query_result.get('LastEvaluatedKey')
            
            next_token = self._encode_next_token(last_evaluated_key) if last_evaluated_key else None
            
            pagination_metadata: PaginationMetadata = {
                'nextToken': next_token,
                'hasMoreResults': last_evaluated_key is not None
            }
            
            return items, pagination_metadata
            
        except ClientError as error:
            self.logger.error(f"Error querying policies: {error}")
            raise error

    def _encode_next_token(self, last_evaluated_key: dict) -> str | None:
        try:
            import json
            import base64
            token_json = json.dumps(last_evaluated_key)
            return base64.b64encode(token_json.encode('utf-8')).decode('utf-8')
        except Exception as e:
            self.logger.warning(f"Failed to encode nextToken: {e}")
            return None
