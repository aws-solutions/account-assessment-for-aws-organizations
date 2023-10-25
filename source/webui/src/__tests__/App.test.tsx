// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import {render, screen} from '@testing-library/react';
import App from '../App';
import {NotificationContext, NotificationContextProvider} from "../contexts/NotificationContext";
import {UserContext} from "../contexts/UserContext";
import {Auth} from "@aws-amplify/auth";
import {newJob} from "./mocks/handlers";
import {server} from "./mocks/server";
import {rest} from "msw";
import userEvent from '@testing-library/user-event';

jest.mock("@aws-amplify/auth");

describe('the landing page', () => {

  let signInMockFunction: jest.Mock;
  let signOutMockFunction: jest.Mock;

  beforeEach(() => {
    signInMockFunction = jest.fn();
    signInMockFunction.mockReturnValue(new Promise(() => true));
    Auth.federatedSignIn = signInMockFunction;

    signOutMockFunction = jest.fn();
    signOutMockFunction.mockReturnValue(new Promise(() => true));
    Auth.signOut = signOutMockFunction;
  })

  describe('when no user is logged in', () => {
    it('should redirect to login via Amplify Auth.federatedSignIn', () => {
      // ARRANGE

      const userContextFalsy = null;

      // ACT
      render(
        <NotificationContextProvider>
          <UserContext.Provider value={userContextFalsy}>
            <App/>
          </UserContext.Provider>
        </NotificationContextProvider>
      );

      // ASSERT
      const redirectMessage = screen.getByText(/Redirecting to login/i);
      expect(redirectMessage).toBeInTheDocument();

      expect(signInMockFunction).toHaveBeenCalledTimes(1);
    });
  })

  describe('when a user is logged in', () => {
    const userEmail = 'John.Doe@example.com';

    beforeEach(() => {
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

      const userContextTruthy = {attributes: {email: userEmail}} as any;
      const notificationContext = {notifications: [], setNotifications: jest.fn()};
      // eslint-disable-next-line testing-library/no-render-in-setup
      render(
        <NotificationContext.Provider value={notificationContext}>
          <UserContext.Provider value={userContextTruthy}>
            <App/>
          </UserContext.Provider>
        </NotificationContext.Provider>
      );
    })

    describe('Sign Out button', () => {

      it('should be displayed after click on the username', async () => {
        // ACT
        await userEvent.click(screen.getByRole('button', {name: userEmail}));

        // ASSERT
        const signOutButton = await screen.findByRole('menuitem', {name: /Sign out/i});
        expect(signOutButton).toBeInTheDocument();

        expect(signOutMockFunction).not.toHaveBeenCalled();
      });


      it('should log out the user', async () => {
        // ARRANGE
        await userEvent.click(screen.getByRole('button', {name: userEmail}));
        const signOutButton = screen.getByRole('menuitem', {name: /Sign out/i});

        // ACT
        await userEvent.click(signOutButton);

        // ASSERT
        expect(signOutMockFunction).toHaveBeenCalled();
      });
    });

    describe('routing', () => {

      it('should display navigation links', () => {
        expect(screen.getByRole('link', {name: /Delegated Admin Accounts/i})).toBeInTheDocument();
        expect(screen.getByRole('link', {name: /Trusted Access/i})).toBeInTheDocument();
        expect(screen.getByRole('link', {name: /Resource-Based Policies/i})).toBeInTheDocument();
        expect(screen.getByRole('link', {name: /Job History/i})).toBeInTheDocument();
      });

      it('should navigate to job history', async () => {
        // ARRANGE

        // ACT
        await userEvent.click(screen.getByText(/Job History/i));

        // ASSERT
        const heading = screen.getByRole('heading', {name: `Job History (2)`});
        expect(heading).toBeInTheDocument();
      });

      it('should navigate to Delegated Admin Accounts', async () => {
        // ARRANGE

        // ACT
        await userEvent.click(screen.getByText(/Delegated Admin Accounts/i));

        // ASSERT
        const heading = screen.getByRole('heading', {name: `Delegated Admin Accounts (0)`});
        expect(heading).toBeInTheDocument();
      });

      it('should navigate to Trusted Access', async () => {
        // ARRANGE

        // ACT
        await userEvent.click(screen.getByText(/Trusted Access/i));

        // ASSERT
        const heading = screen.getByRole('heading', {name: `Trusted Access (0)`});
        expect(heading).toBeInTheDocument();
      });

      it('should navigate to Resource-Based Policies', async () => {
        // ARRANGE

        // ACT
        await userEvent.click(screen.getAllByText(/Resource-Based Policies/i)[0]);

        // ASSERT
        const heading = screen.getByRole('heading', {name: `Resource-Based Policies (0)`});
        expect(heading).toBeInTheDocument();
      });
    })

    describe('when there is a notification', () => {
      it('should display the notification in the Flashbar', () => {
        // ARRANGE
        const userContextTruthy = {attributes: {email: 'John.Doe@example.com'}} as any;
        const notificationContext = {
          notifications: [{
            header: 'Scan in progress',
            content: 'A scan is currently running'
          }], setNotifications: jest.fn()
        };

        // ACT
        render(
          <NotificationContext.Provider value={notificationContext}>
            <UserContext.Provider value={userContextTruthy}>
              <App/>
            </UserContext.Provider>
          </NotificationContext.Provider>
        );

        // ASSERT
        expect(screen.getByText(/Scan in progress/i)).toBeInTheDocument();
        expect(screen.getByText(/A scan is currently running/i)).toBeInTheDocument();
      });
    });

  });
});