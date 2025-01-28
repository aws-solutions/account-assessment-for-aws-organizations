// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {TrustedAccessModel} from "./TrustedAccessModel";
import {TableProps} from "@cloudscape-design/components";
import {formattedDateTime} from "../../util/Formatter";
import {RouterLink} from "../navigation/RouterLink.tsx";


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
    cell: (item) => <RouterLink href={`/jobs/TRUSTED_ACCESS/${item.JobId}`}>{item.JobId}</RouterLink>
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


export const trustedAccessCsvHeader = "Service Principal, Date Enabled, Last Found at";
export const trustedAccessCsvAttributes = ['ServicePrincipal', 'DateEnabled', 'AssessedAt'];