// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import {render, screen, waitFor, within} from '@testing-library/react';
import {compareOptions, ConfigureScanPage} from "../components/resource-based-policies/ConfigureScanPage";
import {NotificationContext} from "../contexts/NotificationContext";
import {MemoryRouter} from "react-router-dom";
import userEvent from "@testing-library/user-event";
import {server} from "./mocks/server";
import {rest} from "msw";
import {newJob, sampleSelectionOptions} from "./mocks/handlers";
import {apiPathResourceBasedPolicies} from "../components/resource-based-policies/ResourceBasedPoliciesDefinitions";

it('compares options for dropdowns', async () => {
  // ARRANGE
  const usEast1 = {value: 'us-east-1'};
  const usWest2 = {value: 'us-west-2'};

  // ASSERT
  expect(compareOptions(usEast1, usWest2)).toEqual(-1);
  expect(compareOptions(usEast1, usEast1)).toEqual(0);
  expect(compareOptions(usWest2, usEast1)).toEqual(1);
});


describe('the ConfigureScanPage', () => {

  it('loads a stored config and populates the form', async () => {
    // ARRANGE
    server.use(
      rest.get('scan-configs', (request, response, context) => {
        return response(
          context.status(200),
          context.json(sampleSelectionOptions),
        )
      })
    );

    const setNotificationsMockFn = jest.fn();
    render(
      <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
        <MemoryRouter>
          <ConfigureScanPage/>
        </MemoryRouter>
      </NotificationContext.Provider>
    );
    const selectConfigCard = screen.getByTitle('Select-Config');
    const editConfigCard = screen.getByTitle('Edit-Config');

    const loadConfigOption = within(selectConfigCard).getByRole('radio', {name: 'Load existing configuration'});

    // ACT
    await userEvent.click(loadConfigOption);
    const selectConfigDropdown = await within(selectConfigCard).findByText("Choose saved configuration");
    await userEvent.click(selectConfigDropdown);
    const sampleConfigOption = await within(selectConfigCard).findByText("Sample-Config-US");
    await userEvent.click(sampleConfigOption);

    // ASSERT
    const config = sampleSelectionOptions.SavedConfigurations[0];
    expect(await within(editConfigCard).findByText(config.AccountIds[0])).toBeInTheDocument();
    expect(await within(editConfigCard).findByText(config.Regions[0])).toBeInTheDocument();
    expect(await within(editConfigCard).findByText(config.ServiceNames[0])).toBeInTheDocument();
  });


  describe('validating the config', () => {

    it('succeeds with accountIds', async () => {
      // ARRANGE
      const activeJob = newJob('RESOURCE_BASED_POLICY');
      activeJob.JobStatus = 'ACTIVE';
      rest.post(apiPathResourceBasedPolicies, (request, response, context) => {
        return response(
          context.status(200),
          context.json(activeJob)
        )
      })

      const setNotificationsMockFn = jest.fn();
      render(
        <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
          <MemoryRouter>
            <ConfigureScanPage/>
          </MemoryRouter>
        </NotificationContext.Provider>
      );
      const startScanButton = screen.getByRole('button', {name: 'Start Scan'});

      const editConfigCard = screen.getByTitle('Edit-Config');
      const accountSelectionStrategyOption = within(editConfigCard).getByRole('radio', {name: 'Accounts IDs specified below'});

      await userEvent.click(accountSelectionStrategyOption);
      const accountIdTextArea = await within(editConfigCard).findByPlaceholderText("111111222222,123456789012");

      // ACT
      await userEvent.click(accountIdTextArea);
      await userEvent.type(accountIdTextArea, '111122223333,555555555555,\n444455556666');
      await userEvent.click(startScanButton)

      // ASSERT
      await waitFor(() => {
        expect(setNotificationsMockFn).toHaveBeenCalledWith([{
          header: 'Scan started',
          content: `Job with ID ${activeJob.JobId} in progress.`,
          dismissible: true,
          onDismiss: expect.anything()
        }])
      });
    });

    it('fails on invalid accountId', async () => {
      // ARRANGE
      const setNotificationsMockFn = jest.fn();
      render(
        <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
          <MemoryRouter>
            <ConfigureScanPage/>
          </MemoryRouter>
        </NotificationContext.Provider>
      );
      const startScanButton = screen.getByRole('button', {name: 'Start Scan'});

      const editConfigCard = screen.getByTitle('Edit-Config');
      const accountSelectionStrategyOption = within(editConfigCard).getByRole('radio', {name: 'Accounts IDs specified below'});


      await userEvent.click(accountSelectionStrategyOption);
      const accountIdTextArea = await within(editConfigCard).findByPlaceholderText("111111222222,123456789012");

      // ACT
      await userEvent.click(accountIdTextArea);
      await userEvent.type(accountIdTextArea, '111122223333,5555555555,\n44445555T666');
      await userEvent.click(startScanButton)

      // ASSERT
      const errorText = "The following entries are not valid AWS account ids: 5555555555, 44445555T666";
      const validationError = await within(editConfigCard).findByText(errorText);
      expect(validationError).toBeInTheDocument()
    });

    it('succeeds with org unit ids', async () => {
      // ARRANGE
      const activeJob = newJob('RESOURCE_BASED_POLICY');
      activeJob.JobStatus = 'ACTIVE';
      rest.post(apiPathResourceBasedPolicies, (request, response, context) => {
        return response(
          context.status(200),
          context.json(activeJob)
        )
      })

      const setNotificationsMockFn = jest.fn();
      render(
        <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
          <MemoryRouter>
            <ConfigureScanPage/>
          </MemoryRouter>
        </NotificationContext.Provider>
      );
      const startScanButton = screen.getByRole('button', {name: 'Start Scan'});

      const editConfigCard = screen.getByTitle('Edit-Config');
      const accountSelectionStrategyOption = within(editConfigCard).getByRole('radio', {name: 'Accounts in organizational units specified below'});

      await userEvent.click(accountSelectionStrategyOption);
      const orgUnitIdTextArea = await within(editConfigCard).findByPlaceholderText("ou-examplerootid111-exampleouid111,ou-examplerootid222-exampleouid222");

      // ACT
      await userEvent.click(orgUnitIdTextArea);
      await userEvent.type(orgUnitIdTextArea, 'ou-1234-12345678,   ou-1234-12345679');
      await userEvent.click(startScanButton)

      // ASSERT
      await waitFor(() => {
        expect(setNotificationsMockFn).toHaveBeenCalledWith([{
          header: 'Scan started',
          content: `Job with ID ${activeJob.JobId} in progress.`,
          dismissible: true,
          onDismiss: expect.anything()
        }])
      });
    });

    it('fails on invalid org unit id', async () => {
      // ARRANGE
      const setNotificationsMockFn = jest.fn();
      render(
        <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
          <MemoryRouter>
            <ConfigureScanPage/>
          </MemoryRouter>
        </NotificationContext.Provider>
      );
      const startScanButton = screen.getByRole('button', {name: 'Start Scan'});

      const editConfigCard = screen.getByTitle('Edit-Config');
      const accountSelectionStrategyOption = within(editConfigCard).getByRole('radio', {name: 'Accounts in organizational units specified below'});

      await userEvent.click(accountSelectionStrategyOption);
      const orgUnitIdTextArea = await within(editConfigCard).findByPlaceholderText("ou-examplerootid111-exampleouid111,ou-examplerootid222-exampleouid222");

      // ACT
      await userEvent.click(orgUnitIdTextArea);
      await userEvent.type(orgUnitIdTextArea, 'ou-abcd, ou-efgh');
      await userEvent.click(startScanButton)

      // ASSERT
      const errorText = "The following entries are not valid organizational unit ids: ou-abcd, ou-efgh";
      const validationError = await within(editConfigCard).findByText(errorText);
      expect(validationError).toBeInTheDocument()
    });
  });


  describe('clicking the scan button', () => {

    it('starts a scan', async () => {
      // ARRANGE
      const activeJob = newJob('RESOURCE_BASED_POLICY');
      activeJob.JobStatus = 'ACTIVE';
      rest.post(apiPathResourceBasedPolicies, (request, response, context) => {
        return response(
          context.status(200),
          context.json(activeJob)
        )
      })

      const setNotificationsMockFn = jest.fn();
      render(
        <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
          <MemoryRouter>
            <ConfigureScanPage/>
          </MemoryRouter>
        </NotificationContext.Provider>
      );

      const startScanButton = screen.getByRole('button', {name: 'Start Scan'});

      // ACT
      await userEvent.click(startScanButton)

      // ASSERT
      await waitFor(() => {
        expect(setNotificationsMockFn).toHaveBeenCalledWith([{
          header: 'Scan started',
          content: `Job with ID ${activeJob.JobId} in progress.`,
          dismissible: true,
          onDismiss: expect.anything()
        }])
      });
    });
    it('renders an error message on failed scan', async () => {
      // ARRANGE
      const activeJob = newJob('RESOURCE_BASED_POLICY');
      activeJob.JobStatus = 'FAILED';
      server.use(
        rest.post(apiPathResourceBasedPolicies, (request, response, context) => {
          return response(
            context.status(200),
            context.json(activeJob)
          )
        })
      )

      const setNotificationsMockFn = jest.fn();
      render(
        <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
          <MemoryRouter>
            <ConfigureScanPage/>
          </MemoryRouter>
        </NotificationContext.Provider>
      );

      const startScanButton = screen.getByRole('button', {name: 'Start Scan'});

      // ACT
      await userEvent.click(startScanButton)

      // ASSERT
      await waitFor(() => {
        expect(setNotificationsMockFn).toHaveBeenCalledWith([{
          header: 'Scan failed',
          content: `Job with ID ${activeJob.JobId} failed. For details please check the Cloudwatch Logs.`,
          type: 'error',
          dismissible: true,
          onDismiss: expect.anything()
        }])
      })
    });

    it('renders an error message on failed http response', async () => {
      // ARRANGE
      const activeJob = newJob('RESOURCE_BASED_POLICY');
      activeJob.JobStatus = 'FAILED';

      server.use(
        rest.post(apiPathResourceBasedPolicies, (request, response, context) => {
          return response(
            context.status(400),
            context.json({
              Error: 'Region not supported',
              Message: 'The following of your requested regions are not supported: us-east-1',
            })
          )
        })
      )

      const setNotificationsMockFn = jest.fn();
      render(
        <NotificationContext.Provider value={{notifications: [], setNotifications: setNotificationsMockFn}}>
          <MemoryRouter>
            <ConfigureScanPage/>
          </MemoryRouter>
        </NotificationContext.Provider>
      );

      const startScanButton = screen.getByRole('button', {name: 'Start Scan'});

      // ACT
      await userEvent.click(startScanButton)

      // ASSERT
      await waitFor(() => {
        expect(setNotificationsMockFn).toHaveBeenCalledWith([{
          header: 'Region not supported',
          content: `The following of your requested regions are not supported: us-east-1`,
          type: 'error',
          dismissible: true,
          onDismiss: expect.anything()
        }])
      })
    });
  })
});
