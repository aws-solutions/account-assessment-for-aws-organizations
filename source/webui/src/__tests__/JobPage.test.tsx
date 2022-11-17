// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import {render, screen, waitFor, waitForElementToBeRemoved, within} from '@testing-library/react';
import {NotificationContext, NotificationContextProvider} from "../contexts/NotificationContext";
import {JobPage} from "../components/jobs/JobPage";
import {MemoryRouter, Route, Routes} from "react-router-dom";
import {server} from "./mocks/server";
import {rest} from "msw";
import {delegatedAdminItems} from "./DelegatedAdminPage.test";
import userEvent from "@testing-library/user-event";
import {trustedAccessItems} from "./TrustedAccessPage.test";
import {newJobDetails, newTaskFailure} from "./mocks/handlers";

describe('the JobPage', () => {

  let setNotificationsMockFn: jest.Mock;
  beforeEach(async () => {
    setNotificationsMockFn = jest.fn();
  })

  it('renders an error when job not found', async () => {
    // ARRANGE
    server.use(
      rest.get('/jobs/:assessmentType/:id', (request, response, context) => {
        return response(
          context.status(400),
          context.json({Error: "Error", Message: "Job not found"})
        )
      }),
    );

    // ACT
    render(
      <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
        <MemoryRouter initialEntries={['/jobs/DELEGATED_ADMIN/5ac32b0e474b44d7b9ef60e5da02eebd']}>
          <Routes>
            <Route path='/jobs/:assessmentType/:id' element={
              <JobPage/>}
            >
            </Route>
          </Routes>
        </MemoryRouter>
      </NotificationContext.Provider>
    );

    // ASSERT
    expect(await screen.findByRole('heading', {name: (/Job Details/i)})).toBeInTheDocument();
    await waitFor(() => {
      expect(setNotificationsMockFn).toHaveBeenLastCalledWith([{
        header: 'Error',
        content: `Job not found`,
        type: 'error',
        dismissible: true,
        onDismiss: expect.any(Function)
      }])
    })
  });


  it('renders a table with delegated admin findings', async () => {
    // ARRANGE
    server.use(
      rest.get('/jobs/:assessmentType/:id', (request, response, context) => {
        return response(
          context.status(200),
          context.json(newJobDetails())
        )
      }),
    )

    // ACT
    render(
      <NotificationContextProvider>
        <MemoryRouter initialEntries={[`/jobs/DELEGATED_ADMIN/${delegatedAdminItems[0].JobId}`]}>
          <Routes>
            <Route path='/jobs/:assessmentType/:id' element={
              <JobPage/>}
            >
            </Route>
          </Routes>
        </MemoryRouter>
      </NotificationContextProvider>
    );

    // ASSERT
    await screen.findByText(/Loading resources/i)
    expect(await screen.findByRole('heading', {name: (/Job Details/i)})).toBeInTheDocument();
    await waitForElementToBeRemoved(() => screen.queryByText(/Loading resources/i))

    const table = screen.getByTitle('FindingsTable');

    expect(await within(table).findByText(delegatedAdminItems[0].ServicePrincipal)).toBeInTheDocument()
    expect(await within(table).findByText(delegatedAdminItems[1].ServicePrincipal)).toBeInTheDocument()
    expect(await within(table).findByText(delegatedAdminItems[2].ServicePrincipal)).toBeInTheDocument()
  });

  it('renders a table with trusted access findings', async () => {
    // ARRANGE
    server.use(
      rest.get('/jobs/:assessmentType/:id', (request, response, context) => {
        return response(
          context.status(200),
          context.json(newJobDetails('TRUSTED_ACCESS', trustedAccessItems[0].JobId, trustedAccessItems))
        )
      }),
    )

    // ACT
    render(
      <NotificationContextProvider>
        <MemoryRouter initialEntries={[`/jobs/TRUSTED_ACCESS/${trustedAccessItems[0].JobId}`]}>
          <Routes>
            <Route path='/jobs/:assessmentType/:id' element={
              <JobPage/>}
            >
            </Route>
          </Routes>
        </MemoryRouter>
      </NotificationContextProvider>
    );

    // ASSERT
    await screen.findByText(/Loading resources/i)
    expect(await screen.findByRole('heading', {name: (/Job Details/i)})).toBeInTheDocument();
    await waitForElementToBeRemoved(() => screen.queryByText(/Loading resources/i))

    const table = screen.getByTitle('FindingsTable');

    expect(await within(table).findByText(/account-management.amazonaws.com/i)).toBeInTheDocument()
  });

  it('renders a table with taskFailures', async () => {
    // ARRANGE
    const assessmentType = 'TRUSTED_ACCESS';
    const jobId = trustedAccessItems[0].JobId;
    const taskFailures = [newTaskFailure(assessmentType, jobId)];
    server.use(
      rest.get('/jobs/:assessmentType/:id', (request, response, context) => {
        return response(
          context.status(200),
          context.json(newJobDetails(assessmentType, jobId, [], taskFailures))
        )
      }),
    )

    // ACT
    render(
      <NotificationContextProvider>
        <MemoryRouter initialEntries={[`/jobs/TRUSTED_ACCESS/${jobId}`]}>
          <Routes>
            <Route path='/jobs/:assessmentType/:id' element={
              <JobPage/>}
            >
            </Route>
          </Routes>
        </MemoryRouter>
      </NotificationContextProvider>
    );

    // ASSERT
    await screen.findByText(/Loading resources/i)
    expect(await screen.findByRole('heading', {name: (/Job Details/i)})).toBeInTheDocument();
    await waitForElementToBeRemoved(() => screen.queryByText(/Loading resources/i))

    const table = screen.getByTitle('FailuresTable');

    expect(await within(table).findByText(taskFailures[0].Error)).toBeInTheDocument()
  });


  it('deletes a job', async () => {
    // ARRANGE
    const setNotificationsMockFn = jest.fn();
    render(
      <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
        <MemoryRouter initialEntries={['/jobs/TRUSTED_ACCESS/5ac32b0e474b44d7b9ef60e5da02eebd']}>
          <Routes>
            <Route path='/jobs/:assessmentType/:id' element={
              <JobPage/>}
            >
            </Route>
          </Routes>
        </MemoryRouter>
      </NotificationContext.Provider>
    );

    const deleteButton = await screen.findByRole('button', {name: 'Delete'});

    // ACT
    await userEvent.click(deleteButton);

    // ASSERT
    expect(await screen.findByText(/Do you want to delete this job and all associated findings?/i)).toBeInTheDocument()

    // ACT
    const confirmButton = await screen.findByRole('button', {name: 'Ok'});
    await userEvent.click(confirmButton);

    // ASSERT
    await waitFor(() => {
      expect(setNotificationsMockFn).toHaveBeenCalledWith([{
        header: 'Job deleted',
        content: `Job with JobId 5ac32b0e474b44d7b9ef60e5da02eebd was deleted successfully.`,
      }])
    })
  });

  it('cancels deletion of a job', async () => {
    // ARRANGE
    const setNotificationsMockFn = jest.fn();
    render(
      <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
        <MemoryRouter initialEntries={['/jobs/TRUSTED_ACCESS/5ac32b0e474b44d7b9ef60e5da02eebd']}>
          <Routes>
            <Route path='/jobs/:assessmentType/:id' element={
              <JobPage/>}
            >
            </Route>
          </Routes>
        </MemoryRouter>
      </NotificationContext.Provider>
    );

    const deleteButton = await screen.findByRole('button', {name: 'Delete'});

    // ACT
    await userEvent.click(deleteButton);
    const confirmButton = await screen.findByRole('button', {name: 'Cancel'});
    await userEvent.click(confirmButton);

    // ASSERT
    await waitFor(() => {
      expect(setNotificationsMockFn).not.toHaveBeenCalledWith([{
        header: 'Job deleted',
        content: `Job with JobId 5ac32b0e474b44d7b9ef60e5da02eebd was deleted successfully.`,
      }])
    })
  });


});