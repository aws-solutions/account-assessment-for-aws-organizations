// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {useCollection} from "@cloudscape-design/collection-hooks";
import Pagination from "@cloudscape-design/components/pagination";
import {ReactElement, useState} from "react";
import Table from "@cloudscape-design/components/table";
import Header from "@cloudscape-design/components/header";
import CollectionPreferences, {CollectionPreferencesProps} from "@cloudscape-design/components/collection-preferences";
import {Box, TableProps, TextFilter} from "@cloudscape-design/components";
import {ColumnDefinition, SortingState} from "./Cloudscape.types.ts";

export interface AssessmentResult {
  JobId: string,
  AssessedAt: string
}

export type TableState = {
  header: string,
  start: number,
  itemsPerPage: number,
  contentDisplayOption?: Array<CollectionPreferencesProps.ContentDisplayItem>,
}

export const pageSizePreference = {
  title: "Items per page",
  options: [
    {
      value: 10,
      label: "10"
    },
    {
      value: 20,
      label: "20"
    },
    {
      value: 50,
      label: "50"
    }
  ]
};

export const createPagination = (
  tableState: TableState,
  setTableState: (t: TableState) => void,
  items: readonly any[]
) =>
  <Pagination
    ariaLabels={{
      nextPageLabel: "Next page",
      previousPageLabel: "Previous page",
      pageLabel: (pageNumber) => `Page ${pageNumber}`
    }}
    currentPageIndex={tableState.start}
    pagesCount={Math.ceil(items.length / tableState.itemsPerPage)}
    onChange={(e) => {
      setTableState({
        ...tableState,
        start: e.detail.currentPageIndex
      });
    }}
    onNextPageClick={(e) => {
      setTableState({
        ...tableState,
        start: e.detail.requestedPageIndex
      });
    }}
    onPreviousPageClick={(e) => {
      setTableState({
        ...tableState,
        start: e.detail.requestedPageIndex
      });
    }}
  />;


export function AssessmentResultTable(props: {
  title: string,
  description?: string,
  data: any[],
  loading: boolean,
  sorting: { defaultState?: TableProps.SortingState<any> },
  headerVariant: any,
  tableVariant: 'container' | 'embedded' | 'borderless' | 'stacked' | 'full-page',
  actions: React.ReactElement<any, string | React.JSXElementConstructor<any>>,
  columnDefinitions: Array<ColumnDefinition<any>>
  contentDisplayOptions?: Array<CollectionPreferencesProps.ContentDisplayOption>
  contentDisplayItems?: Array<CollectionPreferencesProps.ContentDisplayItem>
}) {
  const {
    title,
    description,
    data,
    loading,
    sorting,
    headerVariant,
    tableVariant,
    actions,
    columnDefinitions,
    contentDisplayOptions,
    contentDisplayItems,
  } = props;

  const [tableState, setTableState] = useState<TableState>({
    header: title,
    start: 1,
    itemsPerPage: 20,
    contentDisplayOption: contentDisplayItems
  });

  const {
    items,
    filterProps,
    collectionProps
  } = useCollection(data, {
    filtering: {
      empty: (
        <Box textAlign='center' color='inherit'>
          <b>No resources</b>
          <Box padding={{bottom: 's'}} variant='p' color='inherit'>
            No resources to display.
          </Box>
        </Box>
      ),
      noMatch: (
        <Box textAlign='center' color='inherit'>
          <b>No match</b>
          <Box padding={{bottom: 's'}} variant='p' color='inherit'>
            No resources matched.
          </Box>
        </Box>
      ),
    },
    sorting: sorting,
  });

  const pagination = createPagination(tableState, setTableState, items);

  let preferences = <CollectionPreferences
    title="Preferences"
    pageSizePreference={pageSizePreference}
    preferences={{
      pageSize: tableState.itemsPerPage,
      contentDisplay: contentDisplayItems
    }}
    onConfirm={(e) => {
      setTableState({
        ...tableState,
        itemsPerPage: e.detail.pageSize || 20,
        contentDisplayOption: e.detail.contentDisplay?.map(item => { return {
          id: item.id,
          visible: item.visible
        }})
      });
    }}
    confirmLabel="Confirm"
    cancelLabel="Cancel"
    contentDisplayPreference={{options: contentDisplayOptions? contentDisplayOptions: []}}
  />;

  return <Table
    {...collectionProps}
    header={<Header
      variant={headerVariant}
      actions={actions}
      description={description}
      counter={`(${items.length})`}>
      {tableState.header}
    </Header>}
    variant={tableVariant}
    loading={loading}
    loadingText={'Loading resources'}
    stickyHeader={true}
    resizableColumns={true}
    filter={
      <TextFilter {...filterProps} filteringPlaceholder="Find resources"/>
    }
    preferences={
      preferences
    }
    pagination={pagination}
    columnDefinitions={columnDefinitions.map(it => {
      return {...it, sortingField: it.id}
    })}
    items={items.slice(
      (tableState.start - 1) * tableState.itemsPerPage,
      tableState.start * tableState.itemsPerPage
    )}
    wrapLines={true}
    columnDisplay={tableState.contentDisplayOption}
  ></Table>
}

export function FullPageAssessmentResultTable({
                                                title,
                                                description,
                                                data,
                                                loading,
                                                actions,
                                                columnDefinitions,
                                                defaultSorting
                                              }: {
  title: string,
  description?: string,
  data: any[],
  loading: boolean,
  actions: ReactElement,
  columnDefinitions: Array<ColumnDefinition<any>>,
  defaultSorting?: SortingState<any>
}) {

  const tableVariant = "full-page";
  const headerVariant = "awsui-h1-sticky";
  const sorting = {
    defaultState: defaultSorting || {
      sortingColumn: {sortingField: 'AssessedAt'},
      isDescending: true
    }
  };
  return AssessmentResultTable({
    title,
    description,
    data,
    loading,
    sorting,
    headerVariant,
    tableVariant,
    actions,
    columnDefinitions
  });
}

export function ContainerAssessmentResultTable({title, data, loading, actions, columnDefinitions, contentDisplayOptions, contentDisplayItems}: {
  title: string,
  data: any[],
  loading: boolean,
  actions: ReactElement,
  columnDefinitions: Array<ColumnDefinition<any>>,
  contentDisplayOptions?: Array<CollectionPreferencesProps.ContentDisplayOption>
  contentDisplayItems?: Array<CollectionPreferencesProps.ContentDisplayItem>
}) {

  const tableVariant = "container";
  const headerVariant = "h2";
  const sorting = {};
  return AssessmentResultTable({
    title,
    data,
    loading,
    sorting,
    headerVariant,
    tableVariant,
    actions,
    columnDefinitions,
    contentDisplayOptions,
    contentDisplayItems,
  });
}