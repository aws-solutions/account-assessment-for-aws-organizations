// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {screen, waitForElementToBeRemoved, within} from '@testing-library/react';
import {MOCK_SERVER_URL, server} from "./mocks/server";
import {http} from "msw";
import {ResourceBasedPolicyModel} from "../components/resource-based-policies/ResourceBasedPolicyModel";
import {badRequest, ok} from "./mocks/handlers.ts";
import {renderAppContent} from "./test-utils.tsx";
import {apiPathResourceBasedPolicies} from "../components/resource-based-policies/ResourceBasedPoliciesDefinitions.tsx";

export const resourceBasedPolicyItems: ResourceBasedPolicyModel[] = [
  {
    SortKey: '1',
    AccountId: "111122223333",
    ServiceName: "S3",
    Region: "us-east-1",
    AssessedAt: "2022-07-22T16:47:40.448Z",
    JobId: "3284055467",
  } as ResourceBasedPolicyModel,
  {
    SortKey: '2',
    AccountId: "555555555555",
    ServiceName: "S3",
    Region: "us-east-1",
    AssessedAt: "2022-07-22T16:47:40.448Z",
    JobId: "69565464",
  } as ResourceBasedPolicyModel,
  {
    SortKey: '3',
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
    renderAppContent({
      initialRoute: `/resource-based-policy`,
    });

    // ASSERT
    expect(screen.getByRole('heading', {name: ("Resource-Based Policies (0)")})).toBeInTheDocument();
  });

  it('renders all items from a list of Resource-Based Policies', async () => {
    // ARRANGE
    server.use(
      http.get(MOCK_SERVER_URL + apiPathResourceBasedPolicies, () => {
        return ok({Results: resourceBasedPolicyItems})
      }),
    );

    // ACT
    renderAppContent({
      initialRoute: `/resource-based-policy`,
    });
    await screen.findByText(/Loading resources/i)
    await waitForElementToBeRemoved(screen.queryByText(/Loading resources/i))

    const table = screen.getByRole('table');

    // ASSERT
    expect(await within(table).findByText(/111122223333/i)).toBeInTheDocument();
    expect(await within(table).findByText(/555555555555/i)).toBeInTheDocument();
    expect(await within(table).findByText(/444455556666/i)).toBeInTheDocument();
  });

  it('shows an error notification', async () => {
    // ARRANGE

    server.use(
      http.get(MOCK_SERVER_URL + '/resource-based-policies', () => {
        return badRequest({error: "SomeError", message: "Oops. Something went wrong."})
      }),
    );

    // ACT
    renderAppContent({
      initialRoute: `/resource-based-policy`,
    });
    await screen.findByText(/Loading resources/i)

    // ASSERT
    expect(screen.getByRole('heading', {name: ("Resource-Based Policies (0)")})).toBeInTheDocument();

    const flashbar = await screen.findByTestId('flashbar');
    await within(flashbar).findByText('Unexpected error');
  });
});