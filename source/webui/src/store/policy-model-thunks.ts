// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createAsyncThunk} from '@reduxjs/toolkit';
import {addNotification} from "./notifications-slice.ts";
import {get, ResultList} from "../util/ApiClient.ts";
import {apiPathPolicyExplorer} from "../components/policy-explorer/PolicyExplorerDefinitions.tsx";
import {PolicyModel, PolicySearchModel, QueryStringParams} from "../components/policy-explorer/PolicyExplorerModel.tsx";

const MAX_ALLOWED_RESULTS = 5000;

export const fetchPolicyModels = createAsyncThunk<PolicyModel[], PolicySearchModel>(
  'policyExplorer/fetchPolicyModels',
  async (searchParams, thunkAPI): Promise<PolicyModel[]> => {

    const queryStringParams: QueryStringParams = {
      ...searchParams.filters,
      "region": searchParams.filters.region ?? "GLOBAL",
    };

    const response = (await get<ResultList<PolicyModel>>(`${apiPathPolicyExplorer}/${searchParams.policyType}`, {queryParams: queryStringParams}));

    if (response.error || !response.responseBody?.Results) {
      thunkAPI.dispatch(
        addNotification({
          id: 'get-policy-models-status',
          header: 'Unexpected error',
          content: 'There was a problem getting trusted access data from the backend. Please consult the Troubleshooting section in the documentation.',
          type: 'error',
        }),
      );
      return Promise.reject();
    }

    const results = response.responseBody!.Results;
    if (results.length >= MAX_ALLOWED_RESULTS) {
      thunkAPI.dispatch(
        addNotification({
          id: 'get-policy-models-status',
          header: 'Too many results',
          content: 'We are displaying the first 5,000 results, but there are more results that match your query. Please narrow down the search by setting additional filters.',
          type: 'info',
        }),
      );
    }

    return results;
  }
);
