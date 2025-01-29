// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createEntityAdapter, createSlice, Slice} from '@reduxjs/toolkit';
import {ApiDataState, ApiDataStatus, DEFAULT_INITIAL_STATE} from './types';

import {ResourceBasedPolicyModel} from "../components/resource-based-policies/ResourceBasedPolicyModel.ts";
import {fetchResourceBasedPolicies} from "./resource-based-policies-thunks.ts";

const resourceBasedPoliciesSortComparer = (a: ResourceBasedPolicyModel, b: ResourceBasedPolicyModel) => b.SortKey.localeCompare(a.SortKey);

export const resourceBasedPoliciesAdapter = createEntityAdapter<ResourceBasedPolicyModel, string>({
  sortComparer: resourceBasedPoliciesSortComparer,
  selectId: (it: ResourceBasedPolicyModel) => it.SortKey
});

export const {
  selectAll: selectAllResourceBasedPolicy,
  selectEntities: resourceBasedPoliciesDict,
  selectById: resourceBasedPoliciesById,
  selectIds: resourceBasedPoliciesIds,
} = resourceBasedPoliciesAdapter.getSelectors(
  // define how to get the relevant Slice from the Store: destructure and take the delegatedAdmin property
  ({resourceBasedPolicies}: { resourceBasedPolicies: ApiDataState<ResourceBasedPolicyModel> }) => resourceBasedPolicies,
);

export const resourceBasedPoliciesSlice: Slice<
  ApiDataState<ResourceBasedPolicyModel>,
  {},
  string
> = createSlice({
  name: 'resourceBasedPolicies',
  initialState: resourceBasedPoliciesAdapter.getInitialState({...DEFAULT_INITIAL_STATE}),
  reducers: {
    // add Reducer for custom Actions here
  },
  extraReducers(builder) {
    // Reducers for Thunk Actions
    builder
      .addCase(fetchResourceBasedPolicies.pending, (state, action) => {
        state.status = ApiDataStatus.LOADING;
      })
      .addCase(fetchResourceBasedPolicies.fulfilled, (state, action) => {
        state.status = ApiDataStatus.SUCCEEDED;
        resourceBasedPoliciesAdapter.setAll(state, action.payload);
      })
      .addCase(fetchResourceBasedPolicies.rejected, (state, action) => {
        state.status = ApiDataStatus.FAILED;
        state.error = action.error.message ?? null;
      });
  },
});
