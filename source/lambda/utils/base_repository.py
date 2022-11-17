# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import time
from os import getenv
from typing import TypeVar, Generic, List, TypedDict

from aws.services.dynamodb import DynamoDB


def get_seconds_to_live():
    days_to_live = int(getenv('TIME_TO_LIVE_IN_DAYS') or 90)
    return days_to_live * 24 * 60 * 60


class Clock:
    def current_time_in_ms(self):
        return int(time.time())


class FindingModel(TypedDict):
    PartitionKey: str
    SortKey: str
    JobId: str
    AssessedAt: str
    ExpiresAt: int


T = TypeVar('T')


class BaseRepository(Generic[T]):
    table: DynamoDB

    def __init__(self):
        self.clock = Clock()

    def _calculate_expires_at(self):
        return self.clock.current_time_in_ms() + get_seconds_to_live()

    def find_all_by_job_id(self, job_id) -> List[T]:
        return self.table.find_items_by_secondary_index(
            index_name='JobId',
            key='JobId',
            index_value=job_id
        )
