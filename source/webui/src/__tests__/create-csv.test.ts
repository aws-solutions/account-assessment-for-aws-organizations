// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createCSV} from "../components/policy-explorer/create-csv.ts";
import {policyCsvAttributes, policyCsvHeader} from "../components/policy-explorer/PolicyExplorerDefinitions.tsx";

test('that empty array returns column headers', () => {
  // WHEN
  const actual = createCSV([], policyCsvHeader, policyCsvAttributes);

  // THEN
  expect(actual).toEqual("Account Id, Action, Effect, NotAction, NotResource, Policy Type, Region, Resource, Resource Identifier, Service\n");
})

test('that an attribute is extracted', () => {
  // GIVEN
  const items: any[] = [{
    Action: {S: ""},
    Effect: {S: ""},
    AccountId: {S: "123456789012"},
    NotAction: {S: ""},
    NotResource: {S: ""},
    PartitionKey: {S: ""},
    Region: {S: ""},
    Resource: {S: ""},
    Service: {S: ""},
    Policy: {S: ""},
    ResourceIdentifier: {S: ""},
    SortKey: {S: ""}
  }]

  // WHEN
  const actual = createCSV(items, policyCsvHeader, policyCsvAttributes);

  // THEN
  expect(actual).toEqual("Account Id, Action, Effect, NotAction, NotResource, Policy Type, Region, Resource, Resource Identifier, Service\n" +
    '"123456789012","","","","","","","","",""');
})
test('that quotes & commas are escaped', () => {
  // GIVEN
  const items: any[] = [{
    Action: {S: '["foo", "bar"]'},
    Effect: {S: ""},
    AccountId: {S: "123456789012"},
    NotAction: {S: ""},
    NotResource: {S: ""},
    PartitionKey: {S: ""},
    Region: {S: ""},
    Resource: {S: ""},
    Service: {S: ""},
    Policy: {S: ""},
    ResourceIdentifier: {S: ""},
    SortKey: {S: ""}
  }]

  // WHEN
  const actual = createCSV(items, policyCsvHeader, policyCsvAttributes);

  // THEN
  expect(actual).toEqual("Account Id, Action, Effect, NotAction, NotResource, Policy Type, Region, Resource, Resource Identifier, Service\n" +
    '"123456789012","[""foo"", ""bar""]","","","","","","","",""');
});
