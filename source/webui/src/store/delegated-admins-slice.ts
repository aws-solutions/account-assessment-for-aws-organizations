// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createEntityAdapter, createSlice, Slice} from '@reduxjs/toolkit';
import {ApiDataState, ApiDataStatus, DEFAULT_INITIAL_STATE} from './types';
import {DelegatedAdminModel} from "../components/delegated-admin/DelegatedAdminModel.ts";
import {fetchDelegatedAdmins} from "./delegated-admin-thunks.ts";

/*
 * This file is a blueprint for all Slices in the application.
 * All Slices follow the same pattern, so the other files are not documented the same way.
 * Follow the comments in this file to understand the pattern.
 */

/*
 * So far, the delegatedAdmins Slice does not contain Reducers for regular actions,
 * since Thunk Actions cover all use cases.
 */
type DelegatedAdminsReducers = {
  // add custom reducers here
};

/*
 * Define a sort order for DelegatedAdminModel objects.
 */
const delegatedAdminsSortComparer = (a: DelegatedAdminModel, b: DelegatedAdminModel) => b.SortKey.localeCompare(a.SortKey);

/*
 * The EntityAdapter is an abstraction layer on top of the redux Slice,
 * which generates standard CRUD functions for each entity in our application.
 * By using the EntityAdapter, we don't have to design and implement the Actions and Reducers
 * for all entities by hand.
 */
export const delegatedAdminsAdapter = createEntityAdapter<DelegatedAdminModel, string>({
  sortComparer: delegatedAdminsSortComparer,
  selectId: (it: DelegatedAdminModel) => it.SortKey
});

/*
 * Export any of the EntityAdapter's CRUD methods that are used in the application.
 */
export const {
  selectAll: selectAllDelegatedAdmins,
  selectEntities: selectDelegatedAdminsDict,
  selectById: selectDelegatedAdminById,
  selectIds: selectDelegatedAdminIds,
} = delegatedAdminsAdapter.getSelectors(
  // define how to get the relevant Slice from the Store: destructure and take the delegatedAdmin property
  ({delegatedAdmins}: { delegatedAdmins: ApiDataState<DelegatedAdminModel> }) => delegatedAdmins,
);

/*
 * A Slice is a part of the global Store concerned with one specific feature or entity.
 */
export const delegatedAdminsSlice: Slice<
  ApiDataState<DelegatedAdminModel>,
  DelegatedAdminsReducers,
  string
> = createSlice({
  name: 'delegatedAdmins',
  initialState: delegatedAdminsAdapter.getInitialState({...DEFAULT_INITIAL_STATE}),
  reducers: {
    // add Reducer for custom Actions here
  },
  extraReducers(builder) {
    // Reducers for Thunk Actions
    builder
      .addCase(fetchDelegatedAdmins.pending, (state, action) => {
        state.status = ApiDataStatus.LOADING;
      })
      .addCase(fetchDelegatedAdmins.fulfilled, (state, action) => {
        state.status = ApiDataStatus.SUCCEEDED;
        delegatedAdminsAdapter.setAll(state, action.payload);
      })
      .addCase(fetchDelegatedAdmins.rejected, (state, action) => {
        state.status = ApiDataStatus.FAILED;
        state.error = action.error.message ?? null;
      });
  },
});
