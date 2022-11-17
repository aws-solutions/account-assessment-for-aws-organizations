// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {TableProps} from "@cloudscape-design/components";
import {formattedDateTime} from "../../util/Formatter";
import Link from "@cloudscape-design/components/link";
import {ResourceBasedPolicyModel} from "./ResourceBasedPolicyModel";

export const apiPathResourceBasedPolicies = '/resource-based-policies';

export const resourceBasedPolicyColumns: Array<TableProps.ColumnDefinition<ResourceBasedPolicyModel>> = [
  {
    header: "AccountId",
    id: "AccountId",
    cell: (item) => item.AccountId
  },
  {
    header: "Service Name",
    id: "ServiceName",
    cell: (item) => item.ServiceName
  },
  {
    header: "Resource Name",
    id: "ResourceName",
    cell: (item) => item.ResourceName
  },
  {
    header: "Region",
    id: "Region",
    cell: (item) => item.Region
  },
  {
    header: "Dependency Type",
    id: "DependencyType",
    cell: (item) => item.DependencyType
  },
  {
    header: "Dependency On",
    id: "DependencyOn",
    cell: (item) => item.DependencyOn
  },
  {
    header: "Last Found at",
    id: "AssessedAt",
    cell: (item) => formattedDateTime(item.AssessedAt)
  },
  {
    header: "Last Found at Job Id",
    id: "JobId",
    cell: (item) => <Link href={`/jobs/RESOURCE_BASED_POLICY/${item.JobId}`}>{item.JobId}</Link>
  },
];

export const resourceBasedPolicyColumnsForJob: Array<TableProps.ColumnDefinition<ResourceBasedPolicyModel>> = [
  {
    header: "AccountId",
    id: "AccountId",
    cell: (item) => item.AccountId
  },
  {
    header: "Service Name",
    id: "ServiceName",
    cell: (item) => item.ServiceName
  },
  {
    header: "Resource Name",
    id: "ResourceName",
    cell: (item) => item.ResourceName
  },
  {
    header: "Region",
    id: "Region",
    cell: (item) => item.Region
  },
  {
    header: "Dependency Type",
    id: "DependencyType",
    cell: (item) => item.DependencyType
  },
  {
    header: "Dependency On",
    id: "DependencyOn",
    cell: (item) => item.DependencyOn
  },
];
