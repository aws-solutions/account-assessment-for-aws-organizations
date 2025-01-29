// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {format} from "date-fns";

function escapeValue(attribute: { S: string } | any) {
  if (typeof attribute === 'string') return '"' + attribute.replaceAll('"', '""') + '"';
  if (typeof attribute === 'object' && typeof (attribute as any).S === 'string')
    return '"' + attribute.S.replaceAll('"', '""') + '"';
  else return attribute;
}

export const createCSV = (items: any[], header: string, propertyNames: string[]) => {
  const csvLines = items.map(item => {
    return propertyNames.map(attributeName => {
      console.log(item, attributeName);
      return escapeValue(item[attributeName]);
    }).join(',')
  }).join('\n')

  return header + '\n' + csvLines;
}

export const downloadCSV = (items: Array<any>, filename: string, header: string, propertyNames: string[]) => {
  const searchResults = createCSV(items, header, propertyNames);

  const searchResultsInCsv = new Blob([searchResults], {
    type: 'application/txt'
  });

  const aElement = document.createElement('a');
  const date = format(new Date(), 'yyyy-MM-dd')
  aElement.setAttribute('download', `account-assessment-${date}-${filename}.csv`);
  const href = URL.createObjectURL(searchResultsInCsv);
  aElement.href = href;
  aElement.setAttribute('target', '_blank');
  aElement.click();
  URL.revokeObjectURL(href);
};