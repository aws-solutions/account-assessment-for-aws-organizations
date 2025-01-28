// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createEntityAdapter, createSlice, Slice} from '@reduxjs/toolkit';
import {ApiDataState, ApiDataStatus, DEFAULT_INITIAL_STATE} from './types';
import {PolicyModel} from "../components/policy-explorer/PolicyExplorerModel.tsx";
import {fetchPolicyModels} from "./policy-model-thunks.ts";

const policyModelsSortComparer = (a: PolicyModel, b: PolicyModel) => (a.PartitionKey + b.SortKey).localeCompare(a.PartitionKey + a.SortKey);

export const policyModelsAdapter = createEntityAdapter<PolicyModel, string>({
  sortComparer: policyModelsSortComparer,
  selectId: (it: PolicyModel) => it.PartitionKey + it.SortKey
});

export const {
  selectAll: selectAllPolicyModels,
  selectEntities: selectPolicyModelDict,
  selectById: selectPolicyModelById,
  selectIds: selectPolicyModelIds,
} = policyModelsAdapter.getSelectors(
  ({policyModels}: { policyModels: ApiDataState<PolicyModel> }) => policyModels,
);

export const policyModelsSlice: Slice<
  ApiDataState<PolicyModel>,
  {},
  string
> = createSlice({
  name: 'policyModels',
  initialState: policyModelsAdapter.getInitialState({...DEFAULT_INITIAL_STATE}),
  reducers: {},
  extraReducers(builder) {
    builder
      .addCase(fetchPolicyModels.pending, (state, action) => {
        state.status = ApiDataStatus.LOADING;
      })
      .addCase(fetchPolicyModels.fulfilled, (state, action) => {
        state.status = ApiDataStatus.SUCCEEDED;
        policyModelsAdapter.setAll(state, action.payload);
      })
      .addCase(fetchPolicyModels.rejected, (state, action) => {
        state.status = ApiDataStatus.FAILED;
        state.error = action.error.message ?? null;
      });
  },
});
