// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {screen, waitForElementToBeRemoved, within} from '@testing-library/react';
import {renderAppContent} from "./test-utils.tsx";
import userEvent from "@testing-library/user-event";
import {MOCK_SERVER_URL, server} from "./mocks/server.ts";
import {http} from "msw";
import {apiPathPolicyExplorer} from "../components/policy-explorer/PolicyExplorerDefinitions.tsx";
import {badRequest, ok} from "./mocks/handlers.ts";

describe('the PolicyExplorer search form', () => {

  it('renders the search form', () => {
    // ARRANGE

    // ACT
    renderAppContent({
      initialRoute: `/policy-explorer`,
    });

    // ASSERT
    expect(screen.getByRole('heading', {name: "Policy Explorer"})).toBeInTheDocument();
    expect(screen.getByRole('textbox', {name: "Action"})).toBeInTheDocument();
    expect(screen.queryByRole('textbox', {name: "NotAction"})).not.toBeInTheDocument();
  });

  it('toggles the advanced policy elements', async () => {
    // ARRANGE
    renderAppContent({
      initialRoute: `/policy-explorer`,
    });
    const searchForm = screen.getByTestId('search-criteria');
    const toggle = within(searchForm).getByText(/advanced policy elements/i);

    // ACT
    await userEvent.click(toggle);

    // ASSERT
    expect(screen.queryByRole('textbox', {name: "NotAction"})).toBeInTheDocument();
  });


  it('clears the search form', async () => {
    // ARRANGE
    renderAppContent({
      initialRoute: `/policy-explorer`,
    });
    const actionInput = screen.getByRole('textbox', {name: "Action"});
    await userEvent.type(actionInput, 'foo');
    expect(actionInput).toHaveValue('foo');

    // ACT
    await userEvent.click(screen.getByRole('button', {name: /clear fields/i}));

    // ASSERT
    expect(actionInput).toHaveValue('');
  });

  it('shows Region filter for Resource Based Policies', async () => {
    // ARRANGE
    renderAppContent({
      initialRoute: `/policy-explorer`,
    });
    expect(screen.queryByRole('textbox', {name: "Principal"})).not.toBeInTheDocument();

    const policyTypeRadioGroup = screen.getByTestId('policy-type');
    const resourceBasedPolicyRadio = within(policyTypeRadioGroup).getByRole('radio', {name: /Resource Based Policies/i});

    // ACT
    await userEvent.click(resourceBasedPolicyRadio);

    // ASSERT
    const regionInput = screen.getByRole('textbox', {name: "Region"});
    expect(regionInput).toHaveValue('GLOBAL');
    expect(screen.getByRole('textbox', {name: "Principal"})).toBeInTheDocument();
  });


});

describe('the PolicyExplorer search results', () => {

  it('displays an error notification', async () => {
    // ARRANGE
    renderAppContent({
      initialRoute: `/policy-explorer`,
    });
    server.use(
      http.get(MOCK_SERVER_URL + apiPathPolicyExplorer + '/:policyType', () => {
        return badRequest({error: "SomeError", message: "Oops. Something went wrong."})
      }),
    )

    // ACT
    await userEvent.click(screen.getByRole('button', {name: /search/i}));

    // ASSERT
    await screen.findByText(/Loading resources/i);
    await waitForElementToBeRemoved(screen.queryByText(/Loading resources/i));

    const flashbar = await screen.findByTestId('flashbar');
    await within(flashbar).findByText('Unexpected error');
  });

  it('renders an empty table', async () => {
    // ARRANGE
    renderAppContent({
      initialRoute: `/policy-explorer`,
    });
    server.use(
      http.get(MOCK_SERVER_URL + apiPathPolicyExplorer + '/:policyType', () => {
        return ok({Results: []})
      })
    );

    // ACT
    await userEvent.click(screen.getByRole('button', {name: /search/i}));

    // ASSERT
    expect(await screen.findByRole('heading', {name: 'Policies (0)'})).toBeInTheDocument();
  });

  it('renders a table with policy items and a modal', async () => {
    // ARRANGE
    renderAppContent({
      initialRoute: `/policy-explorer`,
    });
    server.use(
      http.get(MOCK_SERVER_URL + apiPathPolicyExplorer + '/:policyType', () => {
        return ok({Results: policyItems})
      })
    );

    // ACT
    await userEvent.click(screen.getByRole('button', {name: /search/i}));
    await screen.findByText(/Loading resources/i);
    await waitForElementToBeRemoved(screen.queryByText(/Loading resources/i));

    // ASSERT
    const table = await screen.findByTestId("policy-explorer-table");
    expect(await within(table).findByRole('heading', {name: 'Policies (3)'})).toBeInTheDocument();
    const viewButtons = await screen.findAllByRole('button', {name: /view policy/i});

    // ACT
    await userEvent.click(viewButtons[0]);

    // ASSERT
    const policyModal = await screen.findByRole('dialog', {name: 'Policy'});
    expect(policyModal).toHaveTextContent('"Version": "2012-10-17"');
  });
})

const policyItems = [
  {
    "AccountId": "123456789012",
    "Effect": "Allow",
    "ExpiresAt": 1714863631,
    "Resource": "\"arn:aws:s3:::config-bucket-trustedservice-do-not-delete-*\"",
    "Region": "GLOBAL",
    "ResourceIdentifier": "policy/ConfigAccessPolicy",
    "PartitionKey": "IdentityBasedPolicy",
    "Service": "iam",
    "Policy": "{\"Version\": \"2012-10-17\", \"Statement\": [{\"Effect\": \"Allow\", \"Action\": [\"s3:CreateBucket\", \"s3:DeleteBucket\", \"s3:PutBucketPolicy\"], \"Resource\": \"arn:aws:s3:::config-bucket-trustedservice-do-not-delete-*\"}, {\"Effect\": \"Allow\", \"Action\": [\"s3:ListAllMyBuckets\"], \"Resource\": \"arn:aws:s3:::*\"}, {\"Effect\": \"Allow\", \"Action\": [\"config:*\"], \"Resource\": \"*\"}, {\"Effect\": \"Allow\", \"Action\": [\"iam:GetRole\", \"iam:PassRole\", \"iam:CreateServiceLinkedRole\", \"iam:DeleteServiceLinkedRole\", \"iam:GetServiceLinkedRoleDeletionStatus\"], \"Resource\": \"arn:aws:iam::*:role/aws-service-role/config.amazonaws.com/*\"}]}",
    "SortKey": "GLOBAL#iam#123456789012#policy/ConfigAccessPolicy#1",
    "Action": "[\"s3:CreateBucket\", \"s3:DeleteBucket\", \"s3:PutBucketPolicy\"]"
  },
  {
    "AccountId": "123456789012",
    "Effect": "Allow",
    "ExpiresAt": 1714863631,
    "Resource": "\"arn:aws:s3:::*\"",
    "Region": "GLOBAL",
    "ResourceIdentifier": "policy/ConfigAccessPolicy",
    "PartitionKey": "IdentityBasedPolicy",
    "Service": "iam",
    "Policy": "{\"Version\": \"2012-10-17\", \"Statement\": [{\"Effect\": \"Allow\", \"Action\": [\"s3:CreateBucket\", \"s3:DeleteBucket\", \"s3:PutBucketPolicy\"], \"Resource\": \"arn:aws:s3:::config-bucket-trustedservice-do-not-delete-*\"}, {\"Effect\": \"Allow\", \"Action\": [\"s3:ListAllMyBuckets\"], \"Resource\": \"arn:aws:s3:::*\"}, {\"Effect\": \"Allow\", \"Action\": [\"config:*\"], \"Resource\": \"*\"}, {\"Effect\": \"Allow\", \"Action\": [\"iam:GetRole\", \"iam:PassRole\", \"iam:CreateServiceLinkedRole\", \"iam:DeleteServiceLinkedRole\", \"iam:GetServiceLinkedRoleDeletionStatus\"], \"Resource\": \"arn:aws:iam::*:role/aws-service-role/config.amazonaws.com/*\"}]}",
    "SortKey": "GLOBAL#iam#123456789012#policy/ConfigAccessPolicy#2",
    "Action": "[\"s3:ListAllMyBuckets\"]"
  },
  {
    "AccountId": "111111111111",
    "Effect": "Allow",
    "ExpiresAt": 123456789012,
    "Resource": "\"*\"",
    "Region": "GLOBAL",
    "ResourceIdentifier": "policy/ConfigAccessPolicy",
    "PartitionKey": "IdentityBasedPolicy",
    "Service": "iam",
    "Policy": "{\"Version\": \"2012-10-17\", \"Statement\": [{\"Effect\": \"Allow\", \"Action\": [\"s3:CreateBucket\", \"s3:DeleteBucket\", \"s3:PutBucketPolicy\"], \"Resource\": \"arn:aws:s3:::config-bucket-trustedservice-do-not-delete-*\"}, {\"Effect\": \"Allow\", \"Action\": [\"s3:ListAllMyBuckets\"], \"Resource\": \"arn:aws:s3:::*\"}, {\"Effect\": \"Allow\", \"Action\": [\"config:*\"], \"Resource\": \"*\"}, {\"Effect\": \"Allow\", \"Action\": [\"iam:GetRole\", \"iam:PassRole\", \"iam:CreateServiceLinkedRole\", \"iam:DeleteServiceLinkedRole\", \"iam:GetServiceLinkedRoleDeletionStatus\"], \"Resource\": \"arn:aws:iam::*:role/aws-service-role/config.amazonaws.com/*\"}]}",
    "SortKey": "GLOBAL#iam#123456789012#policy/ConfigAccessPolicy#3",
    "Action": "[\"config:*\"]"
  },
]