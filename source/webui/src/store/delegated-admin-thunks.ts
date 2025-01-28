// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createAsyncThunk} from '@reduxjs/toolkit';
import {DelegatedAdminModel} from "../components/delegated-admin/DelegatedAdminModel.ts";
import {apiPathDelegatedAdmins} from "../components/delegated-admin/DelegatedAdminDefinitions.tsx";
import {addNotification} from "./notifications-slice.ts";
import {get, post} from "../util/ApiClient.ts";
import {JobModel} from "../components/jobs/JobModel.ts";

/*
 * A Thunk wraps an async action (in this case, fetching delegated admin records from the API) in a default way,
 * so that we don't have to come up with a custom implementation and duplicate it for each entity.
 *
 * The Thunk dispatches three actions to the Store:
 * 'pending' action before the async function has started
 * 'fulfilled' action when the async function has completed
 * 'rejected' in case the async action throws an error
 *
 * We have to provide one reducer for each of the 3 cases to the Store.
 */
export const fetchDelegatedAdmins = createAsyncThunk(
  'delegatedAdmins/fetchDelegatedAdmins',
  async (_, thunkAPI): Promise<DelegatedAdminModel[]> => {

    const response = await get<{ Results: DelegatedAdminModel[] }>(apiPathDelegatedAdmins, {});

    if (response.error || !response.responseBody?.Results) {
      thunkAPI.dispatch(
        addNotification({
          id: 'get-delegated-admins-status',
          header: 'Unexpected error',
          content: 'There was a problem getting delegated admin data from the backend. Please consult the Troubleshooting section in the documentation.',
          type: 'error',
        }),
      );

      return Promise.reject();
    }

    return response.responseBody.Results;

  },
);

export const startDelegatedAdminsScan = createAsyncThunk(
  'delegatedAdmins/postDelegatedAdmins',
  async (_, thunkAPI): Promise<JobModel> => {

    const response = await post<JobModel>(apiPathDelegatedAdmins, {body: {}});

    if (response.error || !response.responseBody) {
      thunkAPI.dispatch(
        addNotification({
          id: 'get-delegated-admins-status',
          header: 'Unexpected error',
          content: 'There was a problem getting delegated admin data from the backend. Please consult the Troubleshooting section in the documentation.',
          type: 'error',
        }),
      );

      return Promise.reject();
    }

    const job: JobModel = response.responseBody;

    if (job.JobStatus === 'SUCCEEDED') {
      thunkAPI.dispatch(addNotification({
          id: 'post-delegated-admins-status',
          header: 'Scan succeeded',
          content: `Job with ID ${job.JobId} finished successfully.`,
          type: 'success',
        }),
      );
      return job;
    } else if (job.JobStatus === 'FAILED') {
      thunkAPI.dispatch(addNotification({
          id: 'post-delegated-admins-status',
          header: 'Scan failed',
          content: `Job with ID ${job.JobId} finished with failure. For details please check the Cloudwatch Logs.`,
          type: 'error',
        }),
      );
      return Promise.reject();
    } else {
      thunkAPI.dispatch(addNotification({
          id: 'post-delegated-admins-status',
          header: 'Unexpected response',
          content: `Job responded in an unexpected way. For details please check the Cloudwatch Logs.`,
          type: 'info',
        }),
      );
      return Promise.reject();
    }
  },
);
