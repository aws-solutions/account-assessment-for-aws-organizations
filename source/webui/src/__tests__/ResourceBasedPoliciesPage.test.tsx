// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import {render, screen, waitFor, waitForElementToBeRemoved, within} from '@testing-library/react';
import {NotificationContext, NotificationContextProvider} from "../contexts/NotificationContext";
import {MemoryRouter} from "react-router-dom";
import {server} from "./mocks/server";
import {rest} from "msw";
import {ResourceBasedPolicyModel} from "../components/resource-based-policies/ResourceBasedPolicyModel";
import {ResourceBasedPoliciesPage} from "../components/resource-based-policies/ResourceBasedPoliciesPage";

export const resourceBasedPolicyItems: ResourceBasedPolicyModel[] = [
  {
    AccountId: "111122223333",
    ServiceName: "S3",
    Region: "us-east-1",
    AssessedAt: "2022-07-22T16:47:40.448Z",
    JobId: "3284055467",
  } as ResourceBasedPolicyModel,
  {
    AccountId: "555555555555",
    ServiceName: "S3",
    Region: "us-east-1",
    AssessedAt: "2022-07-22T16:47:40.448Z",
    JobId: "69565464",
  } as ResourceBasedPolicyModel,
  {
    AccountId: "444455556666",
    ServiceName: "S3",
    Region: "us-east-1",
    AssessedAt: "2022-07-22T16:47:40.448Z",
    JobId: "3284055467",
  } as ResourceBasedPolicyModel
];

describe('the ResourceBasedPoliciesPage', () => {

  it('renders an empty table', () => {
    // ARRANGE

    // ACT
    render(
      <NotificationContextProvider>
        <MemoryRouter>
          <ResourceBasedPoliciesPage/>
        </MemoryRouter>
      </NotificationContextProvider>
    );

    // ASSERT
    expect(screen.getByRole('button', {name: (/Start Scan/i)})).toBeInTheDocument();
    expect(screen.getByRole('heading', {name: ("Resource-Based Policies (0)")})).toBeInTheDocument();
  });

  it('renders all items from a list of Resource-Based Policies', async () => {
    // ARRANGE
    server.use(
      rest.get('/resource-based-policies', (request, response, context) => {
        return response(
          context.status(200),
          context.json({Results: resourceBasedPolicyItems}),
        )
      }),
    );

    // ACT
    render(
      <NotificationContextProvider>
        <MemoryRouter>
          <ResourceBasedPoliciesPage/>
        </MemoryRouter>
      </NotificationContextProvider>
    );
    await screen.findByText(/Loading resources/i)
    await waitForElementToBeRemoved(() => screen.queryByText(/Loading resources/i))

    const table = screen.getByRole('table');

    // ASSERT
    expect(await within(table).findByText(/111122223333/i)).toBeInTheDocument();
    expect(await within(table).findByText(/555555555555/i)).toBeInTheDocument();
    expect(await within(table).findByText(/444455556666/i)).toBeInTheDocument();
  });

  it('shows a notification when scan is in progress', async () => {
    // ARRANGE
    const setNotificationsMockFn = jest.fn();
    server.use(
      rest.get('/resource-based-policies', (request, response, context) => {
        return response(
          context.status(200),
          context.json({
            Results: resourceBasedPolicyItems,
            ScanInProgress: true,
          }),
        )
      }),
    );

    // ACT
    render(
      <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
        <MemoryRouter>
          <ResourceBasedPoliciesPage/>
        </MemoryRouter>
      </NotificationContext.Provider>
    );
    await screen.findByText(/Loading resources/i)
    await waitForElementToBeRemoved(() => screen.queryByText(/Loading resources/i))

    // ASSERT
    expect(screen.getByRole('button', {name: (/Start Scan/i)})).toBeInTheDocument();
    expect(screen.getByRole('heading', {name: ("Resource-Based Policies (3)")})).toBeInTheDocument();
    await waitFor(() => {
      expect(setNotificationsMockFn).toHaveBeenCalled();
    });
  });

  it('shows an error notification', async () => {
    // ARRANGE
    const setNotificationsMockFn = jest.fn();
    server.use(
      rest.get('/resource-based-policies', (request, response, context) => {
        return response(
          context.status(400),
          context.json({error: "SomeError", message: "Oops. Something went wrong."}),
        )
      }),
    );

    // ACT
    render(
      <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
        <MemoryRouter>
          <ResourceBasedPoliciesPage/>
        </MemoryRouter>
      </NotificationContext.Provider>
    );
    await screen.findByText(/Loading resources/i)
    await waitForElementToBeRemoved(() => screen.queryByText(/Loading resources/i))

    // ASSERT
    expect(screen.getByRole('button', {name: (/Start Scan/i)})).toBeInTheDocument();
    expect(screen.getByRole('heading', {name: ("Resource-Based Policies (0)")})).toBeInTheDocument();
    await waitFor(() => {
      expect(setNotificationsMockFn).toHaveBeenCalled();
    });
  });
});