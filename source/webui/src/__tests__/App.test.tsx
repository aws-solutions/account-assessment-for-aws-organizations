// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import {render, screen} from '@testing-library/react';
import {NotificationContext, NotificationContextProvider} from "../contexts/NotificationContext";
import {UserContext} from "../contexts/UserContext";
import {newJob} from "./mocks/handlers";
import {MOCK_SERVER_URL, server} from "./mocks/server";
import {http, HttpResponse} from 'msw';
import userEvent from '@testing-library/user-event';
import sinon from 'sinon';
import {Provider} from "react-redux";
import {setupStore} from "../store/store.ts";
import {AuthUser} from "aws-amplify/auth";
import App from "../App.tsx";
import {v4} from "uuid";

describe('the landing page', () => {

  describe('when no user is logged in', () => {

    it('should redirect to login via Amplify Auth.federatedSignIn', () => {
      // ARRANGE
      const store = setupStore();
      let signInCalled = false;

      // ACT
      render(
        <Provider store={store}>
          <UserContext.Provider value={{
            orgId: '',
            user: null,
            email: null,
            signOut: () => {
              return Promise.resolve();
            },
            signInWithRedirect: () => {
              signInCalled = true;
              return Promise.resolve();
            }
          }}>
            <NotificationContextProvider>
              <App></App>
            </NotificationContextProvider>
          </UserContext.Provider>
        </Provider>
      )

      // ASSERT
      const redirectMessage = screen.getByText(/Redirecting to login/i);
      expect(redirectMessage).toBeInTheDocument();
      expect(signInCalled).toBeTruthy();
    });
  })

  describe('when a user is logged in', () => {
    const userEmail = 'John.Doe@example.com';
    const userContext = {
      orgId: '',
      user: {
        username: v4(),
      } as AuthUser,
      email: userEmail,
      signOut: () => {
        signOutCalled = true;
        return Promise.resolve();
      },
      signInWithRedirect: () => Promise.resolve(),
    };
    let signOutCalled = false;

    beforeEach(() => {
      const jobs = [
        newJob('DELEGATED_ADMIN'),
        newJob('RESOURCE_BASED_POLICY')
      ];
      server.use(
        http.get(MOCK_SERVER_URL + '/jobs', () => {
          return HttpResponse.json({Results: jobs}, {
            status: 200,
            headers: [['Access-Control-Allow-Origin', '*']],
          })
        })
      )

      const store = setupStore();
      render(
        <Provider store={store}>
          <UserContext.Provider value={userContext}>
            <NotificationContextProvider>
              <App></App>
            </NotificationContextProvider>
          </UserContext.Provider>
        </Provider>
      );
    })

    describe('Sign Out button', () => {

      it('should be displayed after click on the username', async () => {
        // ACT
        await userEvent.click(screen.getByRole('button', {name: userEmail}));

        // ASSERT
        const signOutButton = await screen.findByRole('menuitem', {name: /Sign out/i});
        expect(signOutButton).toBeInTheDocument();
        expect(signOutCalled).toBeFalsy();
      });


      it('should log out the user', async () => {
        // ARRANGE
        await userEvent.click(screen.getByRole('button', {name: userEmail}));
        const signOutButton = screen.getByRole('menuitem', {name: /Sign out/i});

        // ACT
        await userEvent.click(signOutButton);

        // ASSERT
        expect(signOutCalled).toBeTruthy();
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
        // ARRANGE as any;
        const notificationContext = {
          notifications: [{
            header: 'Scan in progress',
            content: 'A scan is currently running'
          }], setNotifications: sinon.spy()
        };

        // ACT
        const store = setupStore();
        render(
          <Provider store={store}>
            <UserContext.Provider value={userContext}>
              <NotificationContext.Provider value={notificationContext}>
                <App></App>
              </NotificationContext.Provider>
            </UserContext.Provider>
          </Provider>
        );

        // ASSERT
        expect(screen.getByText(/Scan in progress/i)).toBeInTheDocument();
        expect(screen.getByText(/A scan is currently running/i)).toBeInTheDocument();
      });
    });
  });
});