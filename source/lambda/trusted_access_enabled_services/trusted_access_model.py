#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import enum
from typing import TypedDict

from utils.base_repository import FindingModel


class PrincipalType(enum.Enum):
    ORGANIZATION = 'Organization'
    ORGANIZATIONAL_UNIT = 'Organizational_Unit'
    ACCOUNT = 'Account'


# Keep in sync with TrustedAccessModel.ts in the UI project
class TrustedAccessCreateRequest(TypedDict):
    ServicePrincipal: str
    DateEnabled: str
    JobId: str
    AssessedAt: str


class TrustedAccessModel(FindingModel):
    ServicePrincipal: str
    DateEnabled: str
