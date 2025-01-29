// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createEntityAdapter, createSlice, Slice} from '@reduxjs/toolkit';
import {ApiDataState, ApiDataStatus, DEFAULT_INITIAL_STATE} from './types';
import {TrustedAccessModel} from "../components/trusted-access/TrustedAccessModel.ts";
import {fetchTrustedAccess} from "./trusted-access-thunks.ts";

const trustedAccessSortComparer = (a: TrustedAccessModel, b: TrustedAccessModel) => b.SortKey.localeCompare(a.SortKey);

export const trustedAccessAdapter = createEntityAdapter<TrustedAccessModel, string>({
  sortComparer: trustedAccessSortComparer,
  selectId: (it: TrustedAccessModel) => it.SortKey
});

export const {
  selectAll: selectAllTrustedAccess,
  selectEntities: trustedAccessDict,
  selectById: trustedAccessById,
  selectIds: trustedAccessIds,
} = trustedAccessAdapter.getSelectors(
  // define how to get the relevant Slice from the Store: destructure and take the delegatedAdmin property
  ({trustedAccess}: { trustedAccess: ApiDataState<TrustedAccessModel> }) => trustedAccess,
);

export const trustedAccessSlice: Slice<
  ApiDataState<TrustedAccessModel>,
  {},
  string
> = createSlice({
  name: 'trustedAccess',
  initialState: trustedAccessAdapter.getInitialState({...DEFAULT_INITIAL_STATE}),
  reducers: {
    // add Reducer for custom Actions here
  },
  extraReducers(builder) {
    // Reducers for Thunk Actions
    builder
      .addCase(fetchTrustedAccess.pending, (state, action) => {
        state.status = ApiDataStatus.LOADING;
      })
      .addCase(fetchTrustedAccess.fulfilled, (state, action) => {
        state.status = ApiDataStatus.SUCCEEDED;
        trustedAccessAdapter.setAll(state, action.payload);
      })
      .addCase(fetchTrustedAccess.rejected, (state, action) => {
        state.status = ApiDataStatus.FAILED;
        state.error = action.error.message ?? null;
      });
  },
});
