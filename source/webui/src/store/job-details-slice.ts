// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createEntityAdapter, createSlice, Slice} from '@reduxjs/toolkit';
import {ApiDataState, ApiDataStatus, DEFAULT_INITIAL_STATE} from "./types.ts";
import {JobDetails} from '../components/jobs/JobModel.ts';
import {fetchJobDetails} from "./job-details-thunks.ts";

type JobDetailsReducers = {};

const jobDetailsSortComparer = (a: JobDetails, b: JobDetails) => b.Job.SortKey.localeCompare(a.Job.SortKey);

export const jobDetailsAdapter = createEntityAdapter<JobDetails, string>({
  sortComparer: jobDetailsSortComparer,
  selectId: (it: JobDetails) => it.Job.SortKey
});

export const {
  selectById: selectJobDetailsById,
} = jobDetailsAdapter.getSelectors(
  ({jobDetails}: { jobDetails: ApiDataState<JobDetails> }) => jobDetails,
);

export const jobDetailsSlice: Slice<
  ApiDataState<JobDetails>,
  JobDetailsReducers,
  string
> = createSlice({
  name: 'jobDetails',
  initialState: jobDetailsAdapter.getInitialState({...DEFAULT_INITIAL_STATE}),
  reducers: {},
  extraReducers(builder) {
    // Reducers for Thunk Actions
    builder
      .addCase(fetchJobDetails.pending, (state, action) => {
        state.status = ApiDataStatus.LOADING;
      })
      .addCase(fetchJobDetails.fulfilled, (state, action) => {
        state.status = ApiDataStatus.SUCCEEDED;
        jobDetailsAdapter.setOne(state, action.payload);
      })
      .addCase(fetchJobDetails.rejected, (state, action) => {
        state.status = ApiDataStatus.FAILED;
        state.error = action.error.message ?? null;
      });
  },
});

