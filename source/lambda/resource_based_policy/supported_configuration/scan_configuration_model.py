# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import TypedDict, List

from typing_extensions import NotRequired


class ScanConfigModel(TypedDict):
    PartitionKey: NotRequired[str]  # constant PARTITION_KEY_SCAN_CONFIGS
    SortKey: NotRequired[str]  # composed of ConfigurationName
    AccountIds: NotRequired[List[str]]
    OrgUnitIds: NotRequired[List[str]]
    Regions: NotRequired[List[str]]
    ServiceNames: NotRequired[List[str]]
    ConfigurationName: NotRequired[str]
    ExpiresAt: int


class ScanConfigCreateRequest(TypedDict):
    AccountIds: NotRequired[List[str]]
    OrgUnitIds: NotRequired[List[str]]
    Regions: NotRequired[List[str]]
    ServiceNames: NotRequired[List[str]]
    ConfigurationName: NotRequired[str]


class ScanModel(TypedDict):
    AccountIds: List[str]
    Regions: List[str]
    ServiceNames: List[str]
