// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

import {MOCK_SERVER_URL, server} from './__tests__/mocks/server'
import {Amplify} from "aws-amplify";

// Establish API mocking before all tests.
beforeAll(() => {
  server.listen({
    onUnhandledRequest: 'error'
  });
  Amplify.configure({
    API: {
      REST: {
        AccountAssessmentApi: {
          "endpoint": MOCK_SERVER_URL
        }, // empty endpoint URL means the mock server is called
      }
    },
  });
})

// Reset any request handlers that we may add during the tests,
// so they don't affect other tests.
afterEach(() => server.resetHandlers())

// Clean up after the tests are finished.
afterAll(() => server.close())