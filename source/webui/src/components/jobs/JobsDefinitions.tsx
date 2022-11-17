// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {JobModel, JobTaskFailure} from "./JobModel";
import {formattedDateTime} from "../../util/Formatter";
import {TableProps} from "@cloudscape-design/components";
import Link from "@cloudscape-design/components/link";

export const apiPathJobs = '/jobs';

export const jobHistoryColumns: Array<TableProps.ColumnDefinition<JobModel>> = [
  {
    header: "Assessment Type",
    id: "AssessmentType",
    cell: (item) => item.AssessmentType
  },
  {
    header: "Job ID",
    id: "JobId",
    cell: (item) => <Link href={`/jobs/${item.AssessmentType}/${item.JobId}`}>{item.JobId}</Link>
  },
  {
    header: "Status",
    id: "JobStatus",
    cell: (item) => item.JobStatus
  },
  {
    header: "Started by",
    id: "StartedBy",
    cell: (item) => item.StartedBy
  },
  {
    header: "Started at",
    id: "StartedAt",
    cell: (item) => formattedDateTime(item.StartedAt)
  },
  {
    header: "Finished at",
    id: "FinishedAt",
    cell: (item) => formattedDateTime(item.FinishedAt) || '-'
  }
];

export const taskFailureColumns: Array<TableProps.ColumnDefinition<JobTaskFailure>> = [
  {
    header: "Service Name",
    id: "ServiceName",
    cell: (item) => item.ServiceName || '-',
    width: '12em'
  },
  {
    header: "AccountId",
    id: "AccountId",
    cell: (item) => item.AccountId || '-',
    width: '10em'
  },
  {
    header: "Region",
    id: "Region",
    cell: (item) => item.Region || '-',
    width: '10em'
  },
  {
    header: "Failed at",
    id: "FailedAt",
    cell: (item) => formattedDateTime(item.FailedAt),
    width: '10em'
  },
  {
    header: "Error",
    id: "Error",
    cell: (item) => item.Error
  },
];