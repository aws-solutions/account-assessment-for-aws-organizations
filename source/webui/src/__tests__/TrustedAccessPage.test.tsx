// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import {render, screen, waitFor, waitForElementToBeRemoved, within} from '@testing-library/react';
import {NotificationContext, NotificationContextProvider} from "../contexts/NotificationContext";
import {MemoryRouter} from "react-router-dom";
import userEvent from "@testing-library/user-event";
import {server} from "./mocks/server";
import {rest} from "msw";
import {newJobId} from "./mocks/handlers";
import {TrustedAccessModel} from "../components/trusted-access/TrustedAccessModel";
import {TrustedAccessPage} from "../components/trusted-access/TrustedAccessPage";

export const trustedAccessItems: TrustedAccessModel[] = [
  {
    AssessedAt: "2022-07-22T16:47:40.448Z",
    JobId: "3284055467",
    ServicePrincipal: "account-management.amazonaws.com",
    DateEnabled: "2017-04-01T03:33:01.085Z",
  },
  {
    AssessedAt: "2022-07-22T16:47:40.448Z",
    JobId: "69565464",
    ServicePrincipal: "audit-manager.amazonaws.com",
    DateEnabled: "2021-11-25T05:32:23.867Z",
  },
  {
    AssessedAt: "2022-07-22T16:47:40.448Z",
    JobId: "3284055467",
    ServicePrincipal: "cfn-stacksets.amazonaws.com",
    DateEnabled: "2019-12-22T06:26:39.702Z",
  }
];

describe('the TrustedAccessPage', () => {

  it('renders an empty table', () => {
    // ARRANGE

    // ACT
    render(
      <NotificationContextProvider>
        <MemoryRouter>
          <TrustedAccessPage/>
        </MemoryRouter>
      </NotificationContextProvider>
    );

    // ASSERT
    expect(screen.getByRole('button', {name: (/Start Scan/i)})).toBeInTheDocument();
    expect(screen.getByRole('heading', {name: ("Trusted Access (0)")})).toBeInTheDocument();
  });


  it('renders all items from a list of Trusted Services', async () => {
    // ARRANGE
    server.use(
      rest.get('/trusted-access', (request, response, context) => {
        return response(
          context.status(200),
          context.json({Results: trustedAccessItems}),
        )
      }),
    );

    // ACT
    render(
      <NotificationContextProvider>
        <MemoryRouter>
          <TrustedAccessPage/>
        </MemoryRouter>
      </NotificationContextProvider>
    );
    await screen.findByText(/Loading resources/i)
    await waitForElementToBeRemoved(() => screen.queryByText(/Loading resources/i))

    const table = screen.getByRole('table');

    // ASSERT
    expect(await within(table).findByText(/account-management.amazonaws.com/i)).toBeInTheDocument();
    expect(await within(table).findByText(/audit-manager.amazonaws.com/i)).toBeInTheDocument();
    expect(await within(table).findByText(/cfn-stacksets.amazonaws.com/i)).toBeInTheDocument();
  });


  it('shows an error notification', async () => {
    // ARRANGE
    const setNotificationsMockFn = jest.fn();
    server.use(
      rest.get('/trusted-access', (request, response, context) => {
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
          <TrustedAccessPage/>
        </MemoryRouter>
      </NotificationContext.Provider>
    );
    await screen.findByText(/Loading resources/i)
    await waitForElementToBeRemoved(() => screen.queryByText(/Loading resources/i))


    // ASSERT
    expect(screen.getByRole('button', {name: (/Start Scan/i)})).toBeInTheDocument();
    expect(screen.getByRole('heading', {name: ("Trusted Access (0)")})).toBeInTheDocument();
    await waitFor(() => {
      expect(setNotificationsMockFn).toHaveBeenCalled();
    });
  });


  describe('starting a scan', () => {

    let setNotificationsMockFn: jest.Mock;
    beforeEach(async () => {
      setNotificationsMockFn = jest.fn();

      // eslint-disable-next-line testing-library/no-render-in-setup
      render(
        <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
          <MemoryRouter>
            <TrustedAccessPage/>
          </MemoryRouter>
        </NotificationContext.Provider>
      );
      await screen.findByText(/Loading resources/i)
      await waitForElementToBeRemoved(() => screen.queryByText(/Loading resources/i))
    })


    it('shows a success message on succeeded scan', async () => {
      // ARRANGE
      server.use(
        rest.post('/trusted-access', (request, response, context) => {
          return response(
            context.status(200),
            context.json({
              AssessmentType: "TRUSTED_ACCESS",
              JobId: newJobId,
              JobStatus: 'SUCCEEDED',
              StartedAt: new Date().toISOString(),
              StartedBy: 'John.Doe@example.com'
            })
          );
        })
      );

      const startScanButton = screen.getByRole('button', {name: 'Start Scan'});

      // ACT
      await userEvent.click(startScanButton)

      // ASSERT
      await waitFor(() => {
        expect(setNotificationsMockFn).toHaveBeenLastCalledWith([{
          header: 'Scan succeeded',
          content: `Job with ID ${newJobId} finished successfully.`,
          type: 'success',
          dismissible: true,
          onDismiss: expect.any(Function)
        }]);
      });
    });

    it('shows an error message on a failed scan', async () => {
      // ARRANGE
      server.use(
        rest.post('/trusted-access', (request, response, context) => {
          return response(
            context.status(200),
            context.json({
              AssessmentType: "TRUSTED_ACCESS",
              JobId: newJobId,
              JobStatus: 'FAILED',
              StartedAt: new Date().toISOString(),
              StartedBy: 'John.Doe@example.com'
            })
          )
        }),
      )

      const startScanButton = screen.getByRole('button', {name: 'Start Scan'});

      // ACT
      await userEvent.click(startScanButton)

      // ASSERT
      await waitFor(() => {
        expect(setNotificationsMockFn).toHaveBeenLastCalledWith([{
          header: 'Scan failed',
          content: `Job with ID ${newJobId} finished with failure. For details please check the Cloudwatch Logs.`,
          type: 'error',
          dismissible: true,
          onDismiss: expect.any(Function)
        }])
      })
    });

    it('shows an error message on an error response', async () => {
      // ARRANGE
      server.use(
        rest.post('/trusted-access', (request, response, context) => {
          return response(
            context.status(400),
            context.json({error: "SomeError", message: "Oops. Something went wrong."}),
          )
        }),
      )

      const startScanButton = screen.getByRole('button', {name: 'Start Scan'});

      // ACT
      await userEvent.click(startScanButton)

      // ASSERT
      await waitFor(() => {
        expect(setNotificationsMockFn).toHaveBeenLastCalledWith([{
          header: 'Error',
          content: `Scan could not be started`,
          type: 'error',
          dismissible: true,
          onDismiss: expect.any(Function)
        }])
      })
    });

  })

});