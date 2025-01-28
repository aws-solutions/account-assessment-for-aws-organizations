// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {fetchAuthSession} from "aws-amplify/auth";
import {Amplify} from "aws-amplify";

export type ApiResponseState<T> = {
  responseBody: T | null,
  error: { Error: string, Message: string } | null,
  loading: boolean
}

export interface ResultList<T> {
  Results: Array<T>
}

export interface DynamoDbQueryResponse<T> {
  Items: Array<T>
}

export const API_NAME = 'AccountAssessmentApi'; // references Amplify-Configuration in aws-export.js

export async function get<T>(
  path: string,
  init: { headers?: any; queryParams?: any } = {}
): Promise<ApiResponseState<T>> {
  try {
    const queryString = new URLSearchParams(init.queryParams).toString();

    const response = await fetch(`${baseUrl()}${path}?${queryString}`, {
      method: "GET",
      headers: {
        ...init.headers,
        Authorization: `Bearer ${(await fetchAuthSession())?.tokens?.accessToken?.toString()}`,
      },
    });
    const responseBody = await response.json();

    if (responseBody.error) {
      console.error(responseBody);
      return {
        responseBody: null, error: responseBody.error, loading: false
      };
    }

    return {
      responseBody: responseBody as T, error: null, loading: false
    };
  } catch (e: any) {
    const errorObject = e.response && e.response.data ? e.response.data : {
      error: "Error",
      message: "An unexpected error occurred."
    };
    return {
      responseBody: null, error: errorObject, loading: false
    };
  }
}

export async function deleteItem<T>(
  path: string,
  init: { headers?: any; queryParams?: any } = {}
): Promise<ApiResponseState<T>> {
  try {
    const queryString = new URLSearchParams(init.queryParams).toString();
    await fetch(`${baseUrl()}${path}?${queryString}`, {
      method: "DELETE",
      headers: {
        ...init.headers,
        Authorization: `Bearer ${(await fetchAuthSession())?.tokens?.accessToken?.toString()}`,
      }
    });
    return {
      responseBody: null, error: null, loading: false
    };
  } catch (e: any) {
    const errorObject = e.response && e.response.data ? e.response.data : {
      error: "Error",
      message: "An unexpected error occurred."
    };
    return {
      responseBody: null, error: errorObject, loading: false
    };
  }
}

function baseUrl(): string {
  const apiConfigs = Amplify.getConfig().API?.REST;
  const endpoint = apiConfigs?.[API_NAME];
  if (!endpoint) {
    throw new Error(`API ${API_NAME} not found in Amplify config`);
  }
  return endpoint.endpoint;
}

export async function post<T>(
  path: string,
  init: { headers?: any; queryParams?: any, body: object }
): Promise<ApiResponseState<T>> {
  const queryString = new URLSearchParams(init.queryParams).toString();
  try {
    const response = await fetch(`${baseUrl()}${path}?${queryString}`, {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
        ...init.headers,
        Authorization: `Bearer ${(await fetchAuthSession())?.tokens?.accessToken?.toString()}`,
      },
      body: JSON.stringify(init.body)
    });
    const responseBody = await response.json();

    if (responseBody.error) {
      console.error(responseBody);
      return {
        responseBody: null, error: responseBody.error, loading: false
      };
    }

    return {
      responseBody: responseBody as T, error: null, loading: false
    };
  } catch (e: any) {
    const errorObject = e.response && e.response.data ? e.response.data : {
      error: "Error",
      message: "An unexpected error occurred."
    };
    return {
      responseBody: null, error: errorObject, loading: false
    };
  }
}