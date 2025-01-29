// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {AssessmentResult} from "../../util/AssessmentResultTable";

export interface TrustedAccessModel extends AssessmentResult {
  ServicePrincipal: string,
  DateEnabled: string,
  SortKey: string
}