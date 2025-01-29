// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createEntityAdapter, createSlice, Slice} from '@reduxjs/toolkit';
import {ApiDataState, ApiDataStatus, DEFAULT_INITIAL_STATE} from "./types.ts";
import {JobModel} from "../components/jobs/JobModel.ts";
import {fetchJobs} from "./jobs-thunks.ts";

type JobReducers = {};

const jobSortComparer = (a: JobModel, b: JobModel) => b.SortKey.localeCompare(a.SortKey);

export const jobAdapter = createEntityAdapter<JobModel, string>({
  sortComparer: jobSortComparer,
  selectId: (it: JobModel) => it.SortKey
});

export const jobsSlice: Slice<
  ApiDataState<JobModel>,
  JobReducers,
  string
> = createSlice({
  name: 'jobs',
  initialState: jobAdapter.getInitialState({...DEFAULT_INITIAL_STATE}),
  reducers: {},
  extraReducers(builder) {
    // Reducers for Thunk Actions
    builder
      .addCase(fetchJobs.pending, (state, action) => {
        state.status = ApiDataStatus.LOADING;
      })
      .addCase(fetchJobs.fulfilled, (state, action) => {
        state.status = ApiDataStatus.SUCCEEDED;
        jobAdapter.setAll(state, action.payload);
      })
      .addCase(fetchJobs.rejected, (state, action) => {
        state.status = ApiDataStatus.FAILED;
        state.error = action.error.message ?? null;
      })
  },
});

