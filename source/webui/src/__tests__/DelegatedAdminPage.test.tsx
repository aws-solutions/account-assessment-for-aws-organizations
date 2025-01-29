// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {screen, waitForElementToBeRemoved, within} from '@testing-library/react';
import {DelegatedAdminModel} from "../components/delegated-admin/DelegatedAdminModel";
import userEvent from "@testing-library/user-event";
import {MOCK_SERVER_URL, server} from "./mocks/server";
import {http} from "msw";
import {badRequest, newJobId, ok} from "./mocks/handlers";
import {renderAppContent} from "./test-utils.tsx";

export const delegatedAdminItems: DelegatedAdminModel[] = [
  {
    SortKey: 'account-management.amazonaws.com#111122223333',
    Arn: "arn:aws:organizations::111122223333:account/o-t1y3bu06fa/275802758920805",
    Name: "Network",
    Status: "ACTIVE",
    JoinedMethod: "CREATED",
    AssessedAt: "2022-07-22T16:47:40.448Z",
    AccountId: "111122223333",
    Email: "John.Doe@example.com",
    ServicePrincipal: "account-management.amazonaws.com",
    JoinedTimestamp: "2018-11-13T01:42:02.332Z",
    DelegationEnabledDate: "2017-04-01T03:33:01.085Z",
    JobId: "3284055467"
  },
  {
    SortKey: 'audit-manager.amazonaws.com#111122223333',
    Arn: "arn:aws:organizations::111122223333:account/o-t1y3bu06fa/275802920805",
    Name: "Network",
    Status: "ACTIVE",
    JoinedMethod: "CREATED",
    AssessedAt: "2022-07-22T16:47:40.448Z",
    AccountId: "111122223333",
    Email: "John.Doe@example.com",
    ServicePrincipal: "audit-manager.amazonaws.com",
    JoinedTimestamp: "2014-05-29T20:49:30.124Z",
    DelegationEnabledDate: "2021-11-25T05:32:23.867Z",
    JobId: "69565464"
  },
  {
    SortKey: 'cfn-stacksets.amazonaws.com#111122223333',
    Arn: "arn:aws:organizations::111122223333:account/o-t1y3bu06fa/275802920805",
    Name: "Network",
    Status: "ACTIVE",
    JoinedMethod: "CREATED",
    AssessedAt: "2022-07-22T16:47:40.448Z",
    AccountId: "111122223333",
    Email: "Jane.Doe@example.com",
    ServicePrincipal: "cfn-stacksets.amazonaws.com",
    JoinedTimestamp: "2014-07-16T14:04:20.472Z",
    DelegationEnabledDate: "2019-12-22T06:26:39.702Z",
    JobId: "3284055467"
  }
];

describe('the DelegatedAdminPage', () => {

  it('renders an empty table', () => {
    // ARRANGE

    // ACT
    renderAppContent({
      initialRoute: '/delegated-admin',
    });

    // ASSERT
    expect(screen.getByRole('button', {name: (/Start Scan/i)})).toBeInTheDocument();
    expect(screen.getByRole('heading', {name: (/Delegated Admin Accounts/i)})).toBeInTheDocument();
  });


  it('renders all items from a list of DelegatedAdmins', async () => {
    // ARRANGE
    server.use(
      http.get(MOCK_SERVER_URL + '/delegated-admins', () => {
        return ok({Results: delegatedAdminItems})
      }),
    );

    // ACT
    renderAppContent({
      initialRoute: '/delegated-admin',
    });
    await screen.findByText(/Loading resources/i);

    const table = screen.getByRole('table');

    // ASSERT
    expect(await within(table).findByText(/account-management.amazonaws.com/i)).toBeInTheDocument();
    expect(await within(table).findByText(/audit-manager.amazonaws.com/i)).toBeInTheDocument();
    expect(await within(table).findByText(/cfn-stacksets.amazonaws.com/i)).toBeInTheDocument();
  });


  it('shows an error notification', async () => {
    // ARRANGE
    server.use(
      http.get(MOCK_SERVER_URL + '/delegated-admins', () => {
        return badRequest({error: "SomeError", message: "Oops. Something went wrong."})
      }),
    );

    // ACT
    renderAppContent({initialRoute: '/delegated-admin'})
    await screen.findByText(/Loading resources/i)
    await waitForElementToBeRemoved(() => screen.queryByText(/Loading resources/i))


    // ASSERT
    expect(screen.getByRole('button', {name: (/Start Scan/i)})).toBeInTheDocument();
    expect(screen.getByRole('heading', {name: (/Delegated Admin Accounts/i)})).toBeInTheDocument();

    const flashbar = await screen.findByTestId('flashbar');
    await within(flashbar).findByText('Unexpected error');
  });


  describe('starting a scan', () => {

    beforeEach(async () => {
      renderAppContent({initialRoute: '/delegated-admin'})
      await screen.findByText(/Loading resources/i)
      await waitForElementToBeRemoved(() => screen.queryByText(/Loading resources/i))
    })


    it('shows a success message on succeeded scan', async () => {
      // ARRANGE
      server.use(
        http.post(MOCK_SERVER_URL + '/delegated-admins', () => {
          return ok({
            AssessmentType: "DELEGATED_ADMIN",
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
        http.post(MOCK_SERVER_URL + '/delegated-admins', () => {
          return ok({
            AssessmentType: "DELEGATED_ADMIN",
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
        http.post(MOCK_SERVER_URL + '/delegated-admins', () => {
          return badRequest({error: "SomeError", message: "Oops. Something went wrong."}
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
