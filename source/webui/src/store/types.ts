// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {EntityState} from '@reduxjs/toolkit';

/**
 * When using custom slices/thunks to load data from the backend, we have to keep of the data loading status.
 */
export enum ApiDataStatus {
  IDLE = 'IDLE',
  LOADING = 'LOADING',
  SUCCEEDED = 'SUCCEEDED',
  FAILED = 'FAILED',
}

export type StatusAndError = {
  status: ApiDataStatus;
  error: string | null;
};
export type ApiDataState<EntityType> = EntityState<EntityType, string> & StatusAndError;

export const DEFAULT_INITIAL_STATE: StatusAndError = {
  status: ApiDataStatus.IDLE,
  error: null,
};
