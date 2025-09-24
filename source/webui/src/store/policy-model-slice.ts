// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createEntityAdapter, createSlice, Slice} from '@reduxjs/toolkit';
import {ApiDataState, ApiDataStatus, DEFAULT_INITIAL_STATE} from './types';
import {PolicyModel, PaginationMetadata} from "../components/policy-explorer/PolicyExplorerModel.tsx";
import {fetchPolicyModels, fetchMorePolicyModels} from "./policy-model-thunks.ts";

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

export interface PolicyModelsState extends ApiDataState<PolicyModel> {
  pagination: PaginationMetadata | undefined;
}

const initialState: PolicyModelsState = policyModelsAdapter.getInitialState({
  ...DEFAULT_INITIAL_STATE, 
  pagination: undefined
});

export const policyModelsSlice = createSlice({
  name: 'policyModels',
  initialState,
  reducers: {
    clearPolicyModels: (state: PolicyModelsState) => {
      policyModelsAdapter.removeAll(state);
      state.pagination = undefined;
    }
  },
  extraReducers(builder) {
    builder
      .addCase(fetchPolicyModels.pending, (state, action) => {
        state.status = ApiDataStatus.LOADING;
      })
      .addCase(fetchPolicyModels.fulfilled, (state, action) => {
        state.status = ApiDataStatus.SUCCEEDED;
        policyModelsAdapter.setAll(state, action.payload.Results);
        state.pagination = action.payload.Pagination;
      })
      .addCase(fetchPolicyModels.rejected, (state, action) => {
        state.status = ApiDataStatus.FAILED;
        state.error = action.error.message ?? null;
      })
      .addCase(fetchMorePolicyModels.pending, (state, action) => {
      })
      .addCase(fetchMorePolicyModels.fulfilled, (state, action) => {
        policyModelsAdapter.upsertMany(state, action.payload.Results);
        state.pagination = action.payload.Pagination;
      })
      .addCase(fetchMorePolicyModels.rejected, (state, action) => {
        state.error = action.error.message ?? null;
      });
  },
});

export const { clearPolicyModels } = policyModelsSlice.actions;