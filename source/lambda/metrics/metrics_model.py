#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from typing import TypedDict


class ScanMetricsDataModel(TypedDict):
    AssessmentType: str  # 'DelegatedAdmin'|'TrustedAccess'|'ResourceBasedPolicy'
    FindingsCount: str
    ServicesCount: str
    AccountsCount: str
    RegionsCount: str


class MetricResponseModel(TypedDict):
    Solution: str
    TimeStamp: str
    UUID: str
    Data: ScanMetricsDataModel
    Version: str


