// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as React from "react";
import {useContext, useEffect, useState} from "react";
import {Button, SpaceBetween} from "@cloudscape-design/components";
import {ApiResponseState, get} from "../../util/ApiClient";
import {NotificationContext} from "../../contexts/NotificationContext";
import {apiPathResourceBasedPolicies, resourceBasedPolicyColumns} from "./ResourceBasedPoliciesDefinitions";
import {FullPageAssessmentResultTable} from "../../util/AssessmentResultTable";
import {ResourceBasedPolicyResultList} from "./ResourceBasedPolicyModel";
import {useNavigate} from "react-router-dom";

export const ResourceBasedPoliciesPage = () => {

  const [apiData, setApiData] = useState<ApiResponseState<ResourceBasedPolicyResultList>>({
    responseBody: null,
    error: null,
    loading: false
  });
  const {setNotifications} = useContext(NotificationContext);
  const navigate = useNavigate();

  const startScan = () => {
    navigate('configure-scan');
  };

  useEffect(() => {
    loadResourceBasedPoliciesFromApi();
  }, []);

  function loadResourceBasedPoliciesFromApi() {
    setApiData({responseBody: null, error: null, loading: true});
    get<ResourceBasedPolicyResultList>(apiPathResourceBasedPolicies).then((result) => {
      setApiData(result);

      if (result.error) {
        setNotifications([{
          header: result.error.Error,
          content: result.error.Message,
          type: 'error',
          dismissible: true,
          onDismiss: () => setNotifications([])
        }]);
      } else if (result.responseBody?.ScanInProgress) {
        setNotifications([{
          header: 'Scan in Progress',
          content: 'The results table will be updated with results while the scan is running.',
          type: 'info',
          dismissible: true,
          onDismiss: () => setNotifications([])
        }]);
      }
    });
  }

  return (
    <FullPageAssessmentResultTable
      title={"Resource-Based Policies"}
      data={apiData.responseBody?.Results || []}
      loading={apiData.loading}
      columnDefinitions={resourceBasedPolicyColumns}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={loadResourceBasedPoliciesFromApi} disabled={apiData.loading}>
            Refresh
          </Button>
          <Button variant={"primary"}
                  onClick={startScan}
                  disabled={!!apiData.error || apiData.responseBody?.ScanInProgress}>Start Scan</Button>
        </SpaceBetween>
      }
    ></FullPageAssessmentResultTable>
  );

}
