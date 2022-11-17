// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import {render, screen, waitFor, waitForElementToBeRemoved, within} from '@testing-library/react';
import {NotificationContext, NotificationContextProvider} from "../contexts/NotificationContext";
import {JobHistoryPage} from '../components/jobs/JobHistoryPage';
import {server} from "./mocks/server";
import {rest} from "msw";
import {newJob} from "./mocks/handlers";

describe('the JobHistoryPage', () => {

  it('renders an empty table', async () => {
    // ARRANGE

    // ACT
    render(
      <NotificationContextProvider>
        <JobHistoryPage/>
      </NotificationContextProvider>
    );

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
      rest.get('/jobs', (request, response, context) => {

        return response(
          context.status(200),
          context.json({Results: jobs}),
        )
      })
    )

    // ACT
    render(
      <NotificationContextProvider>
        <JobHistoryPage/>
      </NotificationContextProvider>
    );

    // ASSERT
    expect(await screen.findByRole('heading', {name: (/Job History/i)})).toBeInTheDocument();
    await screen.findByText(/Loading resources/i)
    await waitForElementToBeRemoved(() => screen.queryByText(/Loading resources/i))

    const table = screen.getByRole('table');
    const rows = await within(table).findAllByRole('row');

    expect(rows).toHaveLength(jobs.length + 1)
    expect(await within(table).findByText(/DELEGATED_ADMIN/i)).toBeInTheDocument();
    expect(await within(table).findByText(/RESOURCE_BASED_POLICY/i)).toBeInTheDocument();
  });


  it('renders an error', async () => {
    // ARRANGE
    server.use(
      rest.get('/jobs', (request, response, context) => {
        return response(
          context.status(400),
          context.json({Error: "Error", Message: "Ooops. Something went wrong."})
        )
      }),
    );
    let setNotificationsMockFn = jest.fn();

    // ACT
    render(
      <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
        <JobHistoryPage/>
      </NotificationContext.Provider>
    );

    // ASSERT
    expect(await screen.findByRole('heading', {name: (/Job History/i)})).toBeInTheDocument();
    await waitFor(() => {
      expect(setNotificationsMockFn).toHaveBeenLastCalledWith([{
        header: 'Error',
        content: `Ooops. Something went wrong.`,
        type: 'error',
        dismissible: true,
        onDismiss: expect.any(Function)
      }])
    })
  });

});