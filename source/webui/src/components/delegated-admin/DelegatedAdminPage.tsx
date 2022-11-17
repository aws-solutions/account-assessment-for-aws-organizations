// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as React from "react";
import {useContext, useEffect, useState} from "react";
import {DelegatedAdminModel} from "./DelegatedAdminModel";
import {Button, SpaceBetween} from "@cloudscape-design/components";
import {NotificationContext} from "../../contexts/NotificationContext";
import {ApiResponseState, get, post, ResultList} from "../../util/ApiClient";
import {JobModel} from "../jobs/JobModel";
import {apiPathDelegatedAdmins, delegatedAdminDefinitions} from "./DelegatedAdminDefinitions";
import {FullPageAssessmentResultTable} from "../../util/AssessmentResultTable";
import {useNavigate} from "react-router-dom";

export const DelegatedAdminPage = () => {

  const [apiData, setApiData] = useState<ApiResponseState<ResultList<DelegatedAdminModel>>>({
    responseBody: {Results: []},
    error: null,
    loading: false
  });
  const [startingScan, setStartingScan] = useState(false);
  const {setNotifications} = useContext(NotificationContext);
  const navigate = useNavigate();

  function loadDelegatedAdminsFromApi() {
    setApiData({responseBody: null, error: null, loading: true});
    get<ResultList<DelegatedAdminModel>>(apiPathDelegatedAdmins).then((result) => {
      setApiData(result);

      if (result.error) {
        setNotifications([{
          header: result.error.Error,
          content: result.error.Message,
          type: 'error',
          dismissible: true,
          onDismiss: () => setNotifications([])
        }]);
      }
    });
  }

  useEffect(() => {
    setNotifications([]);
    loadDelegatedAdminsFromApi();
  }, []);

  const startScan = () => {
    setNotifications([]);
    setStartingScan(true);
    post<JobModel>(apiPathDelegatedAdmins, {response: true, body: {}}).then((state) => {
        if (state.error) {
          setNotifications([{
            header: 'Error',
            content: 'Scan could not be started',
            type: 'error',
            dismissible: true,
            onDismiss: () => setNotifications([])
          }]);
          setStartingScan(false);
          return;
        }

        const job: JobModel | null = state.responseBody;
        if (job?.JobStatus === 'SUCCEEDED') {

          setNotifications([{
            header: 'Scan succeeded',
            content: `Job with ID ${job.JobId} finished successfully.`,
            type: 'success',
            dismissible: true,
            onDismiss: () => setNotifications([])
          }]);
          navigate(`/jobs/${job.AssessmentType}/${job.JobId}`);
        } else if (job?.JobStatus === 'FAILED') {
          setNotifications([{
            header: 'Scan failed',
            content: `Job with ID ${job.JobId} finished with failure. For details please check the Cloudwatch Logs.`,
            type: 'error',
            dismissible: true,
            onDismiss: () => setNotifications([])
          }]);
        } else {
          setNotifications([{
            header: 'Unexpected response',
            content: `Job responded in an unexpected way. For details please check the Cloudwatch Logs.`,
            dismissible: true,
            onDismiss: () => setNotifications([])
          }]);
        }
        setStartingScan(false);
      }
    );
  };

  return (
    <FullPageAssessmentResultTable
      title={"Delegated Admin Accounts"}
      data={apiData.responseBody?.Results || []}
      loading={apiData.loading}
      columnDefinitions={delegatedAdminDefinitions}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={loadDelegatedAdminsFromApi} disabled={apiData.loading}>
            Refresh
          </Button>
          <Button variant={"primary"} loading={startingScan} onClick={startScan}>Start Scan</Button>
        </SpaceBetween>
      }
    ></FullPageAssessmentResultTable>
  );
}
