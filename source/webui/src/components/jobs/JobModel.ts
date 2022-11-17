// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {DelegatedAdminModel} from "../delegated-admin/DelegatedAdminModel";
import {TrustedAccessModel} from "../trusted-access/TrustedAccessModel";
import {ResourceBasedPolicyModel} from "../resource-based-policies/ResourceBasedPolicyModel";

export type JobModel = {
  AssessmentType: string,
  JobId: string,
  StartedAt: string,
  StartedBy: string,
  FinishedAt?: string,
  JobStatus: 'ACTIVE' | 'QUEUED' | 'SUCCEEDED' | 'FAILED',
}

export type JobTaskFailure = {
  AssessmentType: string,
  JobId: string,
  ServiceName: string,
  AccountId: string,
  Region: string,
  FailedAt: string,
  Error: string,
}

export type JobDetails = {
  Job: JobModel,
  Findings: Array<DelegatedAdminModel | TrustedAccessModel | ResourceBasedPolicyModel>,
  TaskFailures: Array<JobTaskFailure>
}