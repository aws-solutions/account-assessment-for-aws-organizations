// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as React from "react";
import {useContext, useEffect, useState} from "react";
import {NotificationContext} from "../../contexts/NotificationContext";
import {ApiResponseState, get, ResultList} from "../../util/ApiClient";
import {JobModel} from "./JobModel";
import {apiPathJobs, jobHistoryColumns} from "./JobsDefinitions";
import {FullPageAssessmentResultTable} from "../../util/AssessmentResultTable";
import {Button} from "@cloudscape-design/components";

export const JobHistoryPage = () => {

  const [apiData, setApiData] = useState<ApiResponseState<ResultList<JobModel>>>({
    responseBody: {Results: []},
    error: null,
    loading: false
  });

  const {setNotifications} = useContext(NotificationContext);

  function loadJobHistoryFromApi() {
    setApiData({responseBody: {Results: []}, error: null, loading: true});
    get<ResultList<JobModel>>(`${apiPathJobs}`).then((result) => {
      setApiData(result);

      if (result.error) {
        setNotifications([{
          header: result.error.Error,
          content: result.error.Message,
          type: 'error',
          dismissible: true,
          onDismiss: () => setNotifications([])
        }]);
      } else {
        setNotifications([]);
      }
    });
  }

  useEffect(() => {
    loadJobHistoryFromApi();
  }, []);

  return (
    <FullPageAssessmentResultTable
      title={"Job History"}
      actions={<>
        <Button iconName="refresh" onClick={loadJobHistoryFromApi} disabled={apiData.loading}>
          Refresh
        </Button>
      </>}
      data={apiData.responseBody?.Results || []}
      loading={apiData.loading}
      columnDefinitions={jobHistoryColumns}
      defaultSorting={{
        sortingColumn: {sortingField: 'StartedAt'},
        isDescending: true
      }}
    ></FullPageAssessmentResultTable>
  );
}
