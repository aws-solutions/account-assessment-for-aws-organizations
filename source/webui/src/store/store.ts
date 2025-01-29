// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {combineReducers, configureStore} from '@reduxjs/toolkit';
import {delegatedAdminsSlice} from "./delegated-admins-slice.ts";
import {trustedAccessSlice} from "./trusted-access-slice.ts";
import {resourceBasedPoliciesSlice} from "./resource-based-policies-slice.ts";
import {policyModelsSlice} from "./policy-model-slice.ts";
import {jobsSlice} from "./jobs-slice.ts";
import {notificationsSlice} from "./notifications-slice.ts";
import {jobDetailsSlice} from "./job-details-slice.ts";

export const rootReducer = combineReducers({
  notifications: notificationsSlice.reducer,
  jobs: jobsSlice.reducer,
  jobDetails: jobDetailsSlice.reducer,
  delegatedAdmins: delegatedAdminsSlice.reducer,
  trustedAccess: trustedAccessSlice.reducer,
  resourceBasedPolicies: resourceBasedPoliciesSlice.reducer,
  policyModels: policyModelsSlice.reducer,
});
export type RootState = ReturnType<typeof rootReducer>;

export const setupStore = (preloadedState?: Partial<RootState>) => {
  return configureStore({
    reducer: rootReducer,
    preloadedState,
  });
};
