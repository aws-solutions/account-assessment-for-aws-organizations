// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {defineConfig} from 'vite';
import {resolve} from 'path';
import react from '@vitejs/plugin-react'
import browserslistToEsbuild from 'browserslist-to-esbuild'
import {CoverageV8Options} from "vitest/node";


const coverageConfig: { provider: 'v8' } & CoverageV8Options = {
  provider: 'v8',
  enabled: true,
  reportsDirectory: resolve(__dirname, './coverage'),
  reporter: ['text', 'html', 'lcov'],
};

// https://vitejs.dev/config/
const config = {
  plugins: [
    react(),
    // visualizer() // only include when needed for development work
  ],
  server: {
    open: true,
    port: 3000,
  },
  build: {
    outDir: resolve(__dirname, './dist'),
    target: browserslistToEsbuild([
      '>0.2%',
      'not dead',
      'not op_mini all'
    ]),
  },
  test: {
    globals: true, // makes describe, it, expect available without import
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.ts'], // runs this file before all tests
    include: ['./src/__tests__/**/*.test.ts?(x)'],
    coverage: coverageConfig,
    maxConcurrency: 1, // set to 1 to run tests serially, one file at a time
    testTimeout: 25000, // 25s test timeout unless specified otherwise in the test suite
  }
};
export default defineConfig(config);
