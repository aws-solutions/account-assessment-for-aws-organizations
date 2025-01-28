// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createAsyncThunk} from "@reduxjs/toolkit";
import {JobDetails} from "../components/jobs/JobModel.ts";
import {get} from "../util/ApiClient.ts";
import {apiPathJobs} from "../components/jobs/JobsDefinitions.tsx";
import {addNotification} from "./notifications-slice.ts";

export const fetchJobDetails = createAsyncThunk(
  'jobs/fetchJobDetails',
  async ({assessmentType, jobId}: { assessmentType: string, jobId: string }, thunkAPI): Promise<JobDetails> => {

    const response = await get<JobDetails>(`${apiPathJobs}/${assessmentType}/${jobId}`);

    if (response.error || !response.responseBody?.Job) {
      thunkAPI.dispatch(
        addNotification({
          id: 'get-job-details-status',
          header: 'Unexpected error',
          content: 'There was a problem getting job details from the backend. Please consult the Troubleshooting section in the documentation.',
          type: 'error',
        }),
      );

      return Promise.reject();
    }

    return response.responseBody;
  },
);
