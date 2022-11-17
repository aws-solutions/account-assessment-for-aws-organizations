// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {TrustedAccessModel} from "./TrustedAccessModel";
import {TableProps} from "@cloudscape-design/components";
import {formattedDateTime} from "../../util/Formatter";
import Link from "@cloudscape-design/components/link";

export const apiPathTrustedAccess = '/trusted-access';

export const trustedAccessColumns: Array<TableProps.ColumnDefinition<TrustedAccessModel>> = [
  {
    header: "Service Principal",
    id: "ServicePrincipal",
    cell: (item) => item.ServicePrincipal
  },
  {
    header: "Date Enabled",
    id: "DateEnabled",
    cell: (item) => formattedDateTime(item.DateEnabled)
  },
  {
    header: "Last Found at",
    id: "AssessedAt",
    cell: (item) => formattedDateTime(item.AssessedAt)
  },
  {
    header: "Last Found at Job Id",
    id: "JobId",
    cell: (item) => <Link href={`/jobs/TRUSTED_ACCESS/${item.JobId}`}>{item.JobId}</Link>
  },
];

export const trustedAccessColumnsForJob: Array<TableProps.ColumnDefinition<TrustedAccessModel>> = [
  {
    header: "Service Principal",
    id: "ServicePrincipal",
    cell: (item) => item.ServicePrincipal
  },
  {
    header: "Date Enabled",
    id: "DateEnabled",
    cell: (item) => formattedDateTime(item.DateEnabled)
  },
];