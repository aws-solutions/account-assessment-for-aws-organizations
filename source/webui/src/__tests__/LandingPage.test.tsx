// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {screen, waitForElementToBeRemoved, within} from "@testing-library/react";
import {newJob, ok} from "./mocks/handlers";
import {MOCK_SERVER_URL, server} from "./mocks/server";
import {http} from 'msw';
import {renderAppContent} from "./test-utils.tsx";

describe('the landing page', () => {
  it('should display the jobs', async () => {
    // ARRANGE
    const jobs = [
      newJob('DELEGATED_ADMIN'),
      newJob('RESOURCE_BASED_POLICY')
    ];
    server.use(
      http.get(MOCK_SERVER_URL + '/jobs', () => {
        return ok({Results: jobs})
      })
    );

    renderAppContent({
      initialRoute: '/',
    });

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