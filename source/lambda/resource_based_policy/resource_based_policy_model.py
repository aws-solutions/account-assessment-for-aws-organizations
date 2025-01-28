# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import TypedDict, List

from utils.base_repository import FindingModel


class ScanModel(TypedDict):
    AccountIds: List[str]
    Regions: List[str]
    ServiceNames: List[str]


class ResourceBasedPolicyRequestModel(TypedDict):
    Scan: ScanModel
    JobId: str


class ResourceBasedPolicyDBModel(FindingModel):
    AccountId: str
    ServiceName: str
    ResourceName: str
    DependencyType: str
    DependencyOn: str
    Region: str


# Keep in sync with ResourceBasedPolicyModel.ts in the UI project
class ResourceBasedPolicyResponseModel(TypedDict):
    AccountId: str
    ServiceName: str
    ResourceName: str
    DependencyType: str
    DependencyOn: str
    JobId: str
    AssessedAt: str
    Region: str