// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createAsyncThunk} from '@reduxjs/toolkit';
import {get, ResultList} from "../util/ApiClient.ts";
import {JobModel} from "../components/jobs/JobModel.ts";
import {apiPathJobs} from "../components/jobs/JobsDefinitions.tsx";
import {addNotification} from "./notifications-slice.ts";

export const fetchJobs = createAsyncThunk(
  'jobs/fetchJobs',
  async (_, thunkAPI): Promise<JobModel[]> => {

    const response = await get<ResultList<JobModel>>(`${apiPathJobs}`);

    if (response.error || !response.responseBody?.Results) {
      thunkAPI.dispatch(
        addNotification({
          id: 'get-jobs-status',
          header: 'Unexpected error',
          content: 'There was a problem getting job history data from the backend. Please consult the Troubleshooting section in the documentation.',
          type: 'error',
        }),
      );

      return Promise.reject();
    }

    return response.responseBody.Results;

  },
);
