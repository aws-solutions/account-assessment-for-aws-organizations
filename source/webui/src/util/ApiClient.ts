// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {API} from "@aws-amplify/api";

export type ApiResponseState<T> = {
    responseBody: T | null,
    error: { Error: string, Message: string } | null,
    loading: boolean
}
export interface ResultList<T> {
    Results: Array<T>
}

const API_NAME = 'AccountAssessmentApi'; // references Amplify-Configuration in aws-export.js

export async function get<T>(
    path: string,
    init: { headers?: any; response?: boolean; queryStringParameters?: any } = {}
): Promise<ApiResponseState<T>> {
    if (init?.response !== false) init.response = true;
    try {
        const response = await API.get(API_NAME, path, init);
        return {
            responseBody: response.data, error: null, loading: false
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
  init: { headers?: any; response?: boolean; queryStringParameters?: any } = {}
): Promise<ApiResponseState<T>> {
    if (init?.response !== false) init.response = true;
    try {
        const response = await API.del(API_NAME, path, init);
        return {
            responseBody: response.data, error: null, loading: false
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

export async function post<T>(
    path: string,
    init: { headers?: any; response: boolean; queryStringParameters?: any, body?: any }
): Promise<ApiResponseState<T>> {
    try {
        const response = await API.post(API_NAME, path, init);
        return {
            responseBody: response.data, error: null, loading: false
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