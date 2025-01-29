// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {screen, waitForElementToBeRemoved, within} from '@testing-library/react';
import userEvent from "@testing-library/user-event";
import {MOCK_SERVER_URL, server} from "./mocks/server";
import {http} from "msw";
import {badRequest, newJobId, ok} from "./mocks/handlers";
import {TrustedAccessModel} from "../components/trusted-access/TrustedAccessModel";
import {renderAppContent} from "./test-utils.tsx";

export const trustedAccessItems: TrustedAccessModel[] = [
  {
    SortKey: 'account-management.amazonaws.com',
    AssessedAt: "2022-07-22T16:47:40.448Z",
    JobId: "3284055467",
    ServicePrincipal: "account-management.amazonaws.com",
    DateEnabled: "2017-04-01T03:33:01.085Z",
  },
  {
    SortKey: 'audit-manager.amazonaws.com',
    AssessedAt: "2022-07-22T16:47:40.448Z",
    JobId: "69565464",
    ServicePrincipal: "audit-manager.amazonaws.com",
    DateEnabled: "2021-11-25T05:32:23.867Z",
  },
  {
    SortKey: 'cfn-stacksets.amazonaws.com',
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
    renderAppContent({
      initialRoute: '/trusted-access',
    });

    // ASSERT
    expect(screen.getByRole('button', {name: (/Start Scan/i)})).toBeInTheDocument();
    expect(screen.getByRole('heading', {name: ("Trusted Access (0)")})).toBeInTheDocument();
  });


  it('renders all items from a list of Trusted Services', async () => {
    // ARRANGE
    server.use(
      http.get(MOCK_SERVER_URL + '/trusted-access', () => {
        return ok({Results: trustedAccessItems})
      }),
    );

    // ACT
    renderAppContent({
      initialRoute: '/trusted-access',
    });
    await screen.findByText(/Loading resources/i)

    const table = screen.getByRole('table');

    // ASSERT
    expect(await within(table).findByText(/account-management.amazonaws.com/i)).toBeInTheDocument();
    expect(await within(table).findByText(/audit-manager.amazonaws.com/i)).toBeInTheDocument();
    expect(await within(table).findByText(/cfn-stacksets.amazonaws.com/i)).toBeInTheDocument();
  });


  it('shows an error notification', async () => {
    // ARRANGE
    server.use(
      http.get(MOCK_SERVER_URL + '/trusted-access', () => {
        return badRequest(
          {error: "SomeError", message: "Oops. Something went wrong."}
        )
      }),
    );

    // ACT
    renderAppContent({
      initialRoute: '/trusted-access',
    });
    await screen.findByText(/Loading resources/i)
    await waitForElementToBeRemoved(() => screen.queryByText(/Loading resources/i))


    // ASSERT
    expect(screen.getByRole('button', {name: (/Start Scan/i)})).toBeInTheDocument();
    expect(screen.getByRole('heading', {name: ("Trusted Access (0)")})).toBeInTheDocument();

    const flashbar = await screen.findByTestId('flashbar');
    await within(flashbar).findByText('Unexpected error');
  });


  describe('starting a scan', () => {

    beforeEach(async () => {
      renderAppContent({
        initialRoute: '/trusted-access',
      });
      await screen.findByText(/Loading resources/i)
      await waitForElementToBeRemoved(() => screen.queryByText(/Loading resources/i))
    })


    it('shows a success message on succeeded scan', async () => {
      // ARRANGE
      server.use(
        http.post(MOCK_SERVER_URL + '/trusted-access', () => {
          return ok({
            AssessmentType: "TRUSTED_ACCESS",
            JobId: newJobId,
            JobStatus: 'SUCCEEDED',
            StartedAt: new Date().toISOString(),
            StartedBy: 'John.Doe@example.com'
          })
        })
      );

      const startScanButton = screen.getByRole('button', {name: 'Start Scan'});

      // ACT
      await userEvent.click(startScanButton)

      // ASSERT
      const flashbar = await screen.findByTestId('flashbar');
      await within(flashbar).findByText(`Job with ID ${newJobId} finished successfully.`);
    });

    it('shows an error message on a failed scan', async () => {
      // ARRANGE
      server.use(
        http.post(MOCK_SERVER_URL + '/trusted-access', () => {
          return ok({
            AssessmentType: "TRUSTED_ACCESS",
            JobId: newJobId,
            JobStatus: 'FAILED',
            StartedAt: new Date().toISOString(),
            StartedBy: 'John.Doe@example.com'
          })
        }),
      )

      const startScanButton = screen.getByRole('button', {name: 'Start Scan'});

      // ACT
      await userEvent.click(startScanButton)

      // ASSERT
      const flashbar = await screen.findByTestId('flashbar');
      await within(flashbar).findByText(`Job with ID ${newJobId} finished with failure. For details please check the Cloudwatch Logs.`);

    });

    it('shows an error message on an error response', async () => {
      // ARRANGE
      server.use(
        http.post(MOCK_SERVER_URL + '/trusted-access', () => {
          return badRequest(
            {error: "SomeError", message: "Oops. Something went wrong."}
          )
        }),
      )

      const startScanButton = screen.getByRole('button', {name: 'Start Scan'});

      // ACT
      await userEvent.click(startScanButton)

      // ASSERT
      const flashbar = await screen.findByTestId('flashbar');
      await within(flashbar).findByText('Unexpected error');
    });
  })
});