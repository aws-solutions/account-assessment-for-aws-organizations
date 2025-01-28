// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {screen, waitForElementToBeRemoved, within} from '@testing-library/react';
import {MOCK_SERVER_URL, server} from "./mocks/server";
import {http} from "msw";
import {badRequest, newJob, ok} from "./mocks/handlers";
import {renderAppContent} from "./test-utils.tsx";

describe('the JobHistoryPage', () => {

  it('renders an empty table', async () => {
    // ARRANGE

    // ACT
    renderAppContent({
      initialRoute: '/jobs',
    });

    // ASSERT
    expect(await screen.findByRole('heading', {name: (/Job History/i)})).toBeInTheDocument();
  });

  it('renders table with 2 jobs', async () => {
    // ARRANGE
    const jobs = [
      newJob('DELEGATED_ADMIN'),
      newJob('RESOURCE_BASED_POLICY')
    ];
    server.use(
      http.get(MOCK_SERVER_URL + '/jobs', () => {
        return ok({Results: jobs})
      })
    )

    // ACT
    renderAppContent({
      initialRoute: '/jobs',
    });

    // ASSERT
    expect(await screen.findByRole('heading', {name: (/Job History/i)})).toBeInTheDocument();
    await screen.findByText(/Loading resources/i);
    await waitForElementToBeRemoved(screen.queryByText(/Loading resources/i));

    const table = screen.getByRole('table');
    const rows = await within(table).findAllByRole('row');

    expect(rows).toHaveLength(jobs.length + 1)
    expect(await within(table).findByText(/DELEGATED_ADMIN/i)).toBeInTheDocument();
    expect(await within(table).findByText(/RESOURCE_BASED_POLICY/i)).toBeInTheDocument();
  });


  it('renders an error', async () => {
    // ARRANGE
    server.use(
      http.get(MOCK_SERVER_URL + '/jobs', () => {
        return badRequest({Error: "Error", Message: "Ooops. Something went wrong."})
      }),
    );


    // ACT
    renderAppContent({
      initialRoute: '/jobs',
    });

    // ASSERT
    expect(await screen.findByRole('heading', {name: (/Job History/i)})).toBeInTheDocument();
    const flashbar = await screen.findByTestId('flashbar');
    await within(flashbar).findByText('Unexpected error');
  });

});