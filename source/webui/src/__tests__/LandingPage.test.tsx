// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {Auth} from "@aws-amplify/auth";
import {render, screen, waitForElementToBeRemoved, within} from "@testing-library/react";
import {NotificationContext} from "../contexts/NotificationContext";
import {newJob} from "./mocks/handlers";
import {server} from "./mocks/server";
import {rest} from "msw";
import React from "react";
import {LandingPage} from "../components/landing-page/LandingPage";

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


describe('the landing page', () => {
  it('should display the jobs', async () => {
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
    );

    const notificationContext = {notifications: [], setNotifications: jest.fn()};
    render(
      <NotificationContext.Provider value={notificationContext}>
        <LandingPage/>
      </NotificationContext.Provider>
    );

    await screen.findByText(/Loading Assessments/i)
    await waitForElementToBeRemoved(() => screen.queryByText(/Loading Assessments/i));

    // ACT
    const cards = await screen.findAllByRole('listitem');

    // ASSERT
    expect(cards).toHaveLength(2);
    expect((within(cards[0]).getByText(/DELEGATED-ADMIN/i))).toBeInTheDocument();
    expect((within(cards[1]).getByText(/RESOURCE-BASED-POLICY/i))).toBeInTheDocument();
  });
});