# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import TypedDict


class MetricsDataModel(TypedDict):
    AssessmentType: str  # 'DelegatedAdmin'|'TrustedAccess'|'ResourceBasedPolicy'
    FindingsCount: str
    ServicesCount: str
    AccountsCount: str
    RegionsCount: str
    Version: str


class MetricResponseModel(TypedDict):
    Solution: str
    TimeStamp: str
    UUID: str
    Data: MetricsDataModel


