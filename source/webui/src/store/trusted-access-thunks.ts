// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createAsyncThunk} from '@reduxjs/toolkit';
import {addNotification} from "./notifications-slice.ts";
import {get, post} from "../util/ApiClient.ts";
import {JobModel} from "../components/jobs/JobModel.ts";
import {TrustedAccessModel} from "../components/trusted-access/TrustedAccessModel.ts";
import {apiPathTrustedAccess} from "../components/trusted-access/TrustedAccessDefinitions.tsx";

export const fetchTrustedAccess = createAsyncThunk(
  'trustedAccess/fetchTrustedAccess',
  async (_, thunkAPI): Promise<TrustedAccessModel[]> => {

    const response = await get<{ Results: TrustedAccessModel[] }>(apiPathTrustedAccess, {});

    if (response.error || !response.responseBody?.Results) {
      thunkAPI.dispatch(
        addNotification({
          id: 'get-trusted-access-status',
          header: 'Unexpected error',
          content: 'There was a problem getting trusted access data from the backend. Please consult the Troubleshooting section in the documentation.',
          type: 'error',
        }),
      );

      return Promise.reject();
    }

    return response.responseBody!.Results;
  },
);

export const startTrustedAccessScan = createAsyncThunk(
  'trustedAccess/postTrustedAccess',
  async (_, thunkAPI): Promise<JobModel> => {

    const response = (await post<JobModel>(apiPathTrustedAccess, {body: {}}));

    if (response.error || !response.responseBody) {
      thunkAPI.dispatch(
        addNotification({
          id: 'post-trusted-access-status',
          header: 'Unexpected error',
          content: 'There was a problem scanning for trusted access accounts.',
          type: 'error',
        }),
      );

      return Promise.reject();
    }

    const job: JobModel = response.responseBody!;
    if (job.JobStatus === 'SUCCEEDED') {
      thunkAPI.dispatch(addNotification({
          id: 'post-trusted-access-status',
          header: 'Scan succeeded',
          content: `Job with ID ${job.JobId} finished successfully.`,
          type: 'success',
        }),
      );
      return job;
    } else if (job.JobStatus === 'FAILED') {
      thunkAPI.dispatch(addNotification({
          id: 'post-trusted-access-status',
          header: 'Scan failed',
          content: `Job with ID ${job.JobId} finished with failure. For details please check the Cloudwatch Logs.`,
          type: 'error',
        }),
      );
      return Promise.reject();
    } else {
      thunkAPI.dispatch(addNotification({
          id: 'post-trusted-access-status',
          header: 'Unexpected response',
          content: `Job responded in an unexpected way. For details please check the Cloudwatch Logs.`,
          type: 'info',
        }),
      );
      return Promise.reject();
    }
  },
);
