# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import enum
from typing import TypedDict, List

from typing_extensions import NotRequired


class JobStatus(enum.Enum):
    ACTIVE = 'ACTIVE'
    QUEUED = 'QUEUED'
    SUCCEEDED = 'SUCCEEDED'
    SUCCEEDED_WITH_FAILED_TASKS = 'SUCCEEDED_WITH_FAILED_TASKS'
    FAILED = 'FAILED'


class AssessmentType(enum.Enum):
    DELEGATED_ADMIN = 'DELEGATED_ADMIN'
    TRUSTED_ACCESS = 'TRUSTED_ACCESS'
    RESOURCE_BASED_POLICY = 'RESOURCE_BASED_POLICY'
    POLICY_EXPLORER = 'POLICY_EXPLORER'


# Keep in sync with JobModel.ts in the UI project
class JobModel(TypedDict):
    PartitionKey: str  # composed of AssessmentType
    SortKey: str  # composed of jobs#JobId
    AssessmentType: str
    JobId: str
    StartedAt: str
    StartedBy: str
    JobStatus: str
    FinishedAt: NotRequired[str]
    ExpiresAt: int
    Error: NotRequired[str]


class JobCreateRequest(TypedDict):
    AssessmentType: str
    StartedAt: str
    StartedBy: str
    JobStatus: str
    FinishedAt: NotRequired[str]
    Error: NotRequired[str]


class JobTaskFailure(TypedDict):
    PartitionKey: str  # taskFailures
    SortKey: str  # composed of assessmentType#JobId#failureId
    JobId: str
    AssessmentType: str
    ServiceName: str
    AccountId: str
    Region: str
    FailedAt: str
    ExpiresAt: int
    Error: str


class JobDetails(TypedDict):
    Job: JobModel
    Findings: List
    TaskFailures: List[JobTaskFailure]


class JobTaskFailureCreateRequest(TypedDict):
    JobId: str
    AssessmentType: str
    ServiceName: str
    AccountId: str
    Region: str
    FailedAt: str
    Error: str


class JobMarkerModel(TypedDict):
    PartitionKey: str
    SortKey: str  # composed of AssessmentType
    AssessmentType: str
    JobStatus: str
    JobId: str
    ExpiresAt: int
