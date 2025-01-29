// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {DelegatedAdminModel} from "./DelegatedAdminModel";
import {formattedDateTime} from "../../util/Formatter";
import {TableProps} from "@cloudscape-design/components";
import {RouterLink} from "../navigation/RouterLink.tsx";

export const apiPathDelegatedAdmins = '/delegated-admins';

export const delegatedAdminDefinitions: Array<TableProps.ColumnDefinition<DelegatedAdminModel>> = [
  {
    header: "Account Id",
    id: "AccountId",
    cell: (item) => item.AccountId,
    width: 150,
  },
  {
    header: "Service Principal",
    id: "ServicePrincipal",
    cell: (item) => item.ServicePrincipal,
    width: 250,
  },
  {
    header: "Account Name",
    id: "Name",
    cell: (item) => item.Name,
    width: 250,
  },
  {
    header: "Last Found at",
    id: "AssessedAt",
    cell: (item) => formattedDateTime(item.AssessedAt),
  },
  {
    header: "Admin Email",
    id: "Email",
    cell: (item) => item.Email
  },
  {
    header: "Joined Method",
    id: "JoinedMethod",
    cell: (item) => item.JoinedMethod
  },
  {
    header: "Status",
    id: "Status",
    cell: (item) => item.Status
  },
  {
    header: "Last Found at Job Id",
    id: "JobId",
    cell: (item) => <RouterLink
      href={`/jobs/DELEGATED_ADMIN/${item.JobId}`}
    >{item.JobId}</RouterLink>
  },
];

export const delegatedAdminColumnsForJob: Array<TableProps.ColumnDefinition<DelegatedAdminModel>> = [
  {
    header: "Account Id",
    id: "AccountId",
    cell: (item) => item.AccountId,
    width: 150,
  },
  {
    header: "Service Principal",
    id: "ServicePrincipal",
    cell: (item) => item.ServicePrincipal,
    width: 250,
  },
  {
    header: "Account Name",
    id: "Name",
    cell: (item) => item.Name,
    width: 250,
  },
  {
    header: "Admin Email",
    id: "Email",
    cell: (item) => item.Email
  },
  {
    header: "Joined Method",
    id: "JoinedMethod",
    cell: (item) => item.JoinedMethod
  },
  {
    header: "Status",
    id: "Status",
    cell: (item) => item.Status
  },
];

export const delegatedAdminCsvHeader = "Account Id, Service Principal, Account Name, Admin Email, Joined Method, Status, Last Found at";
export const delegatedAdminCsvAttributes = ['AccountId', 'ServicePrincipal', 'Name', 'Email', 'JoinedMethod', 'Status', 'AssessedAt'];