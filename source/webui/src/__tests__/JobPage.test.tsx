// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {screen, waitForElementToBeRemoved, within} from '@testing-library/react';
import {MOCK_SERVER_URL, server} from "./mocks/server";
import {http} from "msw";
import {delegatedAdminItems} from "./DelegatedAdminPage.test";
import userEvent from "@testing-library/user-event";
import {trustedAccessItems} from "./TrustedAccessPage.test";
import {badRequest, newJobDetails, newTaskFailure, ok} from "./mocks/handlers";
import {renderAppContent} from "./test-utils.tsx";

describe('the JobPage', () => {

  it('renders an error when job not found', async () => {
    // ARRANGE
    server.use(
      http.get(MOCK_SERVER_URL + '/jobs/:assessmentType/:id', () => {
        return badRequest(
          {Error: "Error", Message: "Job not found"}
        )
      }),
    );

    // ACT
    renderAppContent({
      initialRoute: '/jobs/DELEGATED_ADMIN/5ac32b0e474b44d7b9ef60e5da02eebd',
    });

    // ASSERT
    expect(await screen.findByRole('heading', {name: (/Job Details/i)})).toBeInTheDocument()
    const flashbar = await screen.findByTestId('flashbar');
    await within(flashbar).findByText('Unexpected error');
  });


  it('renders a table with delegated admin findings', async () => {
    // ARRANGE
    server.use(
      http.get(MOCK_SERVER_URL + '/jobs/:assessmentType/:id', () => {
        return ok(newJobDetails(
          'DELEGATED_ADMIN',
          delegatedAdminItems[0].JobId
        ))
      }),
    )

    // ACT
    renderAppContent({
      initialRoute: `/jobs/DELEGATED_ADMIN/${delegatedAdminItems[0].JobId}`,
    });

    // ASSERT
    const jobDetailsContainer = screen.getByTestId('job-details-container');
    within(jobDetailsContainer).getByText(/loading resources/i);

    expect(await screen.findByRole('heading', {name: (/Job Details/i)})).toBeInTheDocument();

    const table = screen.getByTitle('FindingsTable');

    await waitForElementToBeRemoved(within(table).getByText(/loading resources/i));
    expect(await within(table).findByText(delegatedAdminItems[0].ServicePrincipal)).toBeInTheDocument()
    expect(await within(table).findByText(delegatedAdminItems[1].ServicePrincipal)).toBeInTheDocument()
    expect(await within(table).findByText(delegatedAdminItems[2].ServicePrincipal)).toBeInTheDocument()
  });

  it('renders a table with trusted access findings', async () => {
    // ARRANGE
    server.use(
      http.get(MOCK_SERVER_URL + '/jobs/:assessmentType/:id', () => {
        return ok(newJobDetails(
          'TRUSTED_ACCESS',
          trustedAccessItems[0].JobId,
          trustedAccessItems
        ))
      }),
    )

    // ACT
    renderAppContent({
      initialRoute: `/jobs/TRUSTED_ACCESS/${trustedAccessItems[0].JobId}`,
    });

    // ASSERT
    const jobDetailsContainer = screen.getByTestId('job-details-container');
    within(jobDetailsContainer).getByText(/loading resources/i);
    expect(await screen.findByRole('heading', {name: (/Job Details/i)})).toBeInTheDocument();

    const table = screen.getByTitle('FindingsTable');

    await waitForElementToBeRemoved(within(table).getByText(/loading resources/i));
    expect(await within(table).findByText(/account-management.amazonaws.com/i)).toBeInTheDocument()
  });

  it('renders a table with taskFailures', async () => {
    // ARRANGE
    const assessmentType = 'TRUSTED_ACCESS';
    const jobId = trustedAccessItems[0].JobId;
    const taskFailures = [newTaskFailure(assessmentType, jobId)];
    server.use(
      http.get(MOCK_SERVER_URL + '/jobs/:assessmentType/:id', () => {
        return ok(newJobDetails(
          assessmentType,
          jobId,
          [],
          taskFailures
        ))
      }),
    )

    // ACT
    renderAppContent({
      initialRoute: `/jobs/TRUSTED_ACCESS/${jobId}`,
    });

    // ASSERT
    const jobDetailsContainer = screen.getByTestId('job-details-container');
    within(jobDetailsContainer).getByText(/loading resources/i);
    expect(await screen.findByRole('heading', {name: (/Job Details/i)})).toBeInTheDocument();

    const table = await screen.findByTitle('FailuresTable');
    expect(await within(table).findByText(taskFailures[0].Error)).toBeInTheDocument()
  });


  it('deletes a job', async () => {
    // ARRANGE

    renderAppContent({
      initialRoute: `/jobs/TRUSTED_ACCESS/5ac32b0e474b44d7b9ef60e5da02eebd`,
    });
    const deleteButton = await screen.findByRole('button', {name: 'Delete'});

    // ACT
    await userEvent.click(deleteButton);

    // ASSERT
    expect(await screen.findByText(/Do you want to delete this job and all associated findings?/i)).toBeInTheDocument()

    // ACT
    const confirmButton = await screen.findByRole('button', {name: 'Ok'});
    await userEvent.click(confirmButton);

    // ASSERT
    const flashbar = await screen.findByTestId('flashbar');
    await within(flashbar).findByText(`Job with JobId 5ac32b0e474b44d7b9ef60e5da02eebd was deleted successfully.`);
  });

  it('cancels deletion of a job', async () => {
    // ARRANGE
    renderAppContent({
      initialRoute: `/jobs/TRUSTED_ACCESS/5ac32b0e474b44d7b9ef60e5da02eebd`,
    });

    const deleteButton = await screen.findByRole('button', {name: 'Delete'});

    // ACT
    await userEvent.click(deleteButton);
    const confirmButton = await screen.findByRole('button', {name: 'Cancel'});
    await userEvent.click(confirmButton);

    // ASSERT
    const flashbar = await screen.findByTestId('flashbar');
    expect(within(flashbar).queryByText(`deleted`)).not.toBeInTheDocument();
  });
});