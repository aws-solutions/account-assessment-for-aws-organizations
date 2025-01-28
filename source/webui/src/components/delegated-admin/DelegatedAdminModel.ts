// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {AssessmentResult} from "../../util/AssessmentResultTable";

export interface DelegatedAdminModel extends AssessmentResult {
  AccountId: string,
  ServicePrincipal: string,
  Arn: string,
  Email: string,
  Name: string,
  Status: string
  JoinedMethod: string,
  JoinedTimestamp: string,
  DelegationEnabledDate: string
  SortKey: string
}