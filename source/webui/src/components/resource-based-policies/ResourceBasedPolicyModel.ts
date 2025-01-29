// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {AssessmentResult} from "../../util/AssessmentResultTable";

export interface ResourceBasedPolicyModel extends AssessmentResult {
  AccountId: string,
  ServiceName: string,
  ResourceName: string,
  Region: string,
  DependencyType: string,
  DependencyOn: string,
  SortKey: string;
}

export type ConfigurationModel = {
  ConfigurationName?: string,
  Regions?: Array<string>,
  ServiceNames?: Array<string>,
  AccountIds?: Array<string>
  OrgUnitIds?: Array<string>
}

export type RegionModel = {
  Region: string,
  RegionName: string,
}
export type ServiceModel = {
  ServiceName: string,
  ServicePrincipal: string,
  FriendlyName: string,
}