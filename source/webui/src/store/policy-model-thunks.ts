// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createAsyncThunk} from '@reduxjs/toolkit';
import {addNotification} from "./notifications-slice.ts";
import {get} from "../util/ApiClient.ts";
import {apiPathPolicyExplorer} from "../components/policy-explorer/PolicyExplorerDefinitions.tsx";
import {PolicySearchModel, QueryStringParams, PolicySearchResponse, PaginationParams} from "../components/policy-explorer/PolicyExplorerModel.tsx";

const buildPaginationParams = (pagination?: PaginationParams): Partial<QueryStringParams> => {
  const params: Partial<QueryStringParams> = {};
  if (pagination?.maxResults) {
    params.maxResults = pagination.maxResults.toString();
  }
  if (pagination?.nextToken) {
    params.nextToken = pagination.nextToken;
  }
  return params;
};

export const fetchPolicyModels = createAsyncThunk<PolicySearchResponse, PolicySearchModel>(
  'policyExplorer/fetchPolicyModels',
  async (searchParams, thunkAPI): Promise<PolicySearchResponse> => {

    const queryStringParams: QueryStringParams = {
      ...searchParams.filters,
      "region": searchParams.filters.region ?? "GLOBAL",
    };

    Object.assign(queryStringParams, buildPaginationParams(searchParams.pagination));

    const response = (await get<PolicySearchResponse>(`${apiPathPolicyExplorer}/${searchParams.policyType}`, {queryParams: queryStringParams}));

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

    return response.responseBody!;
  }
);

export const fetchMorePolicyModels = createAsyncThunk<PolicySearchResponse, PolicySearchModel>(
  'policyExplorer/fetchMorePolicyModels',
  async (searchParams, thunkAPI): Promise<PolicySearchResponse> => {

    const queryStringParams: QueryStringParams = {
      ...searchParams.filters,
      "region": searchParams.filters.region ?? "GLOBAL",
    };

    Object.assign(queryStringParams, buildPaginationParams(searchParams.pagination));

    const response = (await get<PolicySearchResponse>(`${apiPathPolicyExplorer}/${searchParams.policyType}`, {queryParams: queryStringParams}));

    if (response.error || !response.responseBody?.Results) {
      thunkAPI.dispatch(
        addNotification({
          id: 'get-more-policy-models-status',
          header: 'Unexpected error',
          content: 'There was a problem getting additional policy data from the backend.',
          type: 'error',
        }),
      );
      return Promise.reject();
    }

    return response.responseBody!;
  }
);
