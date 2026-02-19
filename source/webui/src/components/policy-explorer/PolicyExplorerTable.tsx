// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {Box, Button, SpaceBetween, TableProps, TextFilter} from "@cloudscape-design/components";
import {
  contentDisplayOptions,
  policyCsvAttributes,
  policyCsvHeader,
  policySearchColumns
} from "./PolicyExplorerDefinitions";
import {PolicyModel, PolicyTypes, FiltersForPolicySearch} from "./PolicyExplorerModel";
import {downloadCSV} from "./create-csv.ts";
import {useSelector, useDispatch} from "react-redux";
import {ApiDataStatus} from "../../store/types.ts";
import CollectionPreferences, {CollectionPreferencesProps} from "@cloudscape-design/components/collection-preferences";
import Table from "@cloudscape-design/components/table";
import Header from "@cloudscape-design/components/header";
import {useCollection} from "@cloudscape-design/collection-hooks";
import {selectAllPolicyModels, PolicyModelsState} from "../../store/policy-model-slice.ts";
import {fetchMorePolicyModels} from "../../store/policy-model-thunks.ts";

export type LastSearchParams = {
  policyType: PolicyTypes;
  filters: FiltersForPolicySearch;
};

export type ContentDisplayOption = CollectionPreferencesProps.ContentDisplayItem;

export const PolicyExplorerTable = ({lastSearchParams, contentDisplayOption, setContentDisplayOption}: {
  lastSearchParams?: LastSearchParams,
  contentDisplayOption?: ContentDisplayOption[],
  setContentDisplayOption?: (options: ContentDisplayOption[]) => void
}) => {
  const columnDefinitions: TableProps.ColumnDefinition<PolicyModel>[] = policySearchColumns;
  const dispatch = useDispatch<any>();

  const policyModelsData = useSelector(
    ({policyModels}: { policyModels: PolicyModelsState }) => policyModels,
  );
  const data = useSelector(selectAllPolicyModels);

  const downloadSearchResults = async () => {
    if (data) downloadCSV(data, 'policy-search-results', policyCsvHeader, policyCsvAttributes);
  }

  const {
    items: filteredItems,
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
        const itemAsString = Object.values(item).join(' ');
        return itemAsString.includes(filteringText);
      }
    },
  });

  const hasMoreResults = policyModelsData.pagination?.hasMoreResults ?? false;
  const isLoadingMore = policyModelsData.loadingMore ?? false;
  const nextToken = policyModelsData.pagination?.nextToken;
  const canFetchMore = hasMoreResults && lastSearchParams && nextToken;

  const handleLoadMore = () => {
    if (!lastSearchParams || !nextToken) return;
    dispatch(fetchMorePolicyModels({
      policyType: lastSearchParams.policyType,
      filters: lastSearchParams.filters,
      pagination: {
        maxResults: 1000,
        nextToken
      }
    }));
  };

  const preferences = <CollectionPreferences
    title="Preferences"
    preferences={{
      contentDisplay: contentDisplayOption
    }}
    onConfirm={(e) => {
      if (setContentDisplayOption && e.detail.contentDisplay) {
        setContentDisplayOption(e.detail.contentDisplay.map(item => ({
          id: item.id,
          visible: item.visible
        })));
      }
    }}
    confirmLabel="Confirm"
    cancelLabel="Cancel"
    contentDisplayPreference={{options: contentDisplayOptions ? contentDisplayOptions : []}}
  />;

  const header = <Header
    variant={'h2'}
    actions={
      <SpaceBetween direction="horizontal" size="xs">
        <Button data-testid="download" variant="normal" onClick={downloadSearchResults}>
          Download Results
        </Button>
      </SpaceBetween>
    }
    counter={`(${filteredItems.length}${hasMoreResults ? '+' : ''})`}
  >
    Policies
  </Header>;

  if (policyModelsData.status === ApiDataStatus.IDLE || policyModelsData.status === ApiDataStatus.FAILED) return <></>;

  return <SpaceBetween size="s">
    <Table
      {...collectionProps}
      data-testid="policy-explorer-table"
      header={header}
      variant={'container'}
      loading={policyModelsData.status === ApiDataStatus.LOADING || isLoadingMore}
      loadingText={'Loading resources'}
      stickyHeader={true}
      resizableColumns={true}
      filter={
        <TextFilter {...filterProps} filteringPlaceholder="Filter search results"/>
      }
      preferences={preferences}
      columnDefinitions={columnDefinitions}
      items={filteredItems}
      wrapLines={true}
      columnDisplay={contentDisplayOption}
    />
    {canFetchMore && (
      <Box textAlign="center">
        <Button
          data-testid="load-more"
          onClick={handleLoadMore}
          loading={isLoadingMore}
        >
          Load More Results
        </Button>
      </Box>
    )}
  </SpaceBetween>
}
