# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import TypedDict

from utils.base_repository import FindingModel


# Keep in sync with DelegatedAdminModel.ts in the UI project
class DelegatedAdminModel(FindingModel):
    AccountId: str
    ServicePrincipal: str
    Arn: str
    Email: str
    Name: str
    Status: str
    JoinedMethod: str
    JoinedTimestamp: str
    DelegationEnabledDate: str


class DelegatedAdminCreateRequest(TypedDict):
    AccountId: str
    ServicePrincipal: str
    Arn: str
    Email: str
    Name: str
    Status: str
    JoinedMethod: str
    JoinedTimestamp: str
    DelegationEnabledDate: str
    JobId: str
    AssessedAt: str
