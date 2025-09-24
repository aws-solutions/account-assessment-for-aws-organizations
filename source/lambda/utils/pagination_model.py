#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from typing import TypedDict, List, TypeVar, Generic

T = TypeVar('T')

class PaginationParams(TypedDict):
    maxResults: int | None
    nextToken: str | None

class PaginationMetadata(TypedDict):
    nextToken: str | None
    hasMoreResults: bool

class PaginatedResponse(TypedDict, Generic[T]):
    Results: List[T]
    Pagination: PaginationMetadata

class DdbPagination(TypedDict):
    Limit: int
    ExclusiveStartKey: str | None
