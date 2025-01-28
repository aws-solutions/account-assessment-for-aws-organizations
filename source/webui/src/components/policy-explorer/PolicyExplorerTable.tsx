// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {Box, Button, TableProps, TextFilter} from "@cloudscape-design/components";
import {
  contentDisplayOptions,
  policyCsvAttributes,
  policyCsvHeader,
  policySearchColumns
} from "./PolicyExplorerDefinitions";
import {PolicyModel} from "./PolicyExplorerModel";
import {createPagination, pageSizePreference, TableState} from "../../util/AssessmentResultTable";
import {downloadCSV} from "./create-csv.ts";
import {useSelector} from "react-redux";
import {ApiDataState, ApiDataStatus} from "../../store/types.ts";
import {Dispatch, SetStateAction} from "react";
import CollectionPreferences from "@cloudscape-design/components/collection-preferences";
import Table from "@cloudscape-design/components/table";
import Header from "@cloudscape-design/components/header";
import {useCollection} from "@cloudscape-design/collection-hooks";
import {selectAllPolicyModels} from "../../store/policy-model-slice.ts";

export const PolicyExplorerTable = ({tableState, setTableState}: {
  tableState: TableState,
  setTableState: Dispatch<SetStateAction<TableState>>
}) => {
  const columnDefinitions: TableProps.ColumnDefinition<PolicyModel>[] = policySearchColumns;

  const policyModelsData = useSelector(
    ({policyModels}: { policyModels: ApiDataState<PolicyModel> }) => policyModels,
  );
  const data = useSelector(selectAllPolicyModels);

  const downloadSearchResults = async () => {
    if (data) downloadCSV(data, 'policy-search-results', policyCsvHeader, policyCsvAttributes);
  }


  const {
    items,
    filterProps,
    collectionProps
  } = useCollection<PolicyModel>(data, {
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
      filteringFunction: (item, filteringText) => {
        if (!filteringText) return true;
        // consider all fields of the item. stringify search term to allow to match escaped characters
        const itemAsString = Object.values(item).join(' ');
        return itemAsString.includes(filteringText);
      }
    },
  });

  const pagination = createPagination(tableState, setTableState, items);

  const preferences = <CollectionPreferences
    title="Preferences"
    pageSizePreference={pageSizePreference}
    preferences={{
      pageSize: tableState.itemsPerPage,
      contentDisplay: tableState.contentDisplayOption
    }}
    onConfirm={(e) => {

      const newPreferences = {
        ...tableState,
        itemsPerPage: e.detail.pageSize || 20,
        contentDisplayOption: e.detail.contentDisplay?.map(item => {
          return {
            id: item.id,
            visible: item.visible
          }
        })
      };
      setTableState(newPreferences);

    }}
    confirmLabel="Confirm"
    cancelLabel="Cancel"
    contentDisplayPreference={{options: contentDisplayOptions ? contentDisplayOptions : []}}
  />;

  const header = <Header
    variant={'h2'}
    actions={
      <Button data-testid="download" variant="normal" onClick={downloadSearchResults}>
        Download Results
      </Button>}
    counter={`(${items.length})`}>
    {tableState.header}
  </Header>;

  if (policyModelsData.status === ApiDataStatus.IDLE || policyModelsData.status === ApiDataStatus.FAILED) return <></>;

  return <Table
    {...collectionProps}
    data-testid="policy-explorer-table"
    header={header}
    variant={'container'}
    loading={policyModelsData.status === ApiDataStatus.LOADING}
    loadingText={'Loading resources'}
    stickyHeader={true}
    resizableColumns={true}
    filter={
      <TextFilter {...filterProps} filteringPlaceholder="Filter search results"/>
    }
    preferences={
      preferences
    }
    pagination={pagination}
    columnDefinitions={columnDefinitions}
    items={items.slice(
      (tableState.start - 1) * tableState.itemsPerPage,
      tableState.start * tableState.itemsPerPage
    )}
    wrapLines={true}
    columnDisplay={tableState.contentDisplayOption}
  ></Table>
}
