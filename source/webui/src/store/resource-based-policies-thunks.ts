// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createAsyncThunk} from '@reduxjs/toolkit';
import {addNotification} from "./notifications-slice.ts";
import {get} from "../util/ApiClient.ts";
import {ResourceBasedPolicyModel} from "../components/resource-based-policies/ResourceBasedPolicyModel.ts";
import {apiPathResourceBasedPolicies} from "../components/resource-based-policies/ResourceBasedPoliciesDefinitions.tsx";

export const fetchResourceBasedPolicies = createAsyncThunk(
  'resourceBasedPolicies/fetchResourceBasedPolicies',
  async (_, thunkAPI): Promise<ResourceBasedPolicyModel[]> => {

    const response = await get<{ Results: ResourceBasedPolicyModel[] }>(apiPathResourceBasedPolicies, {});

    if (response.error || !response.responseBody) {
      thunkAPI.dispatch(
        addNotification({
          id: 'get-resource-based-policies-status',
          header: 'Unexpected error',
          content: 'There was a problem getting resource based policies data from the backend. Please consult the Troubleshooting section in the documentation.',
          type: 'error',
        }),
      );

      return Promise.reject();
    }

    return response.responseBody!.Results;
  },
);
