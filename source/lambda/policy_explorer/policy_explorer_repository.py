#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os
from logging import Logger
from typing import List

from botocore.exceptions import ClientError

from aws.services.dynamodb import DynamoDB
from policy_explorer.policy_explorer_model import DynamoDBPolicyItem, PolicyFilters, PolicyItem, DdbPagination


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
                                pagination: DdbPagination) -> List[PolicyItem]:
        return self.table.query(policy_type, region, filters, pagination)
