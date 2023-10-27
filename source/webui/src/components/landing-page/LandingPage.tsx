// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {Box, Cards, CardsProps, ContentLayout, Link} from "@cloudscape-design/components";
import * as React from "react";
import {useContext, useEffect, useState} from "react";
import {ApiResponseState, get, ResultList} from "../../util/ApiClient";
import {JobModel} from "../jobs/JobModel";
import {NotificationContext} from "../../contexts/NotificationContext";
import {apiPathJobs} from "../jobs/JobsDefinitions";
import Header from "@cloudscape-design/components/header";
import {formattedDateTime} from "../../util/Formatter";

function HeaderComponent({item}: {
  item: JobModel }) {
    let assessmentType = item.AssessmentType;
      while (assessmentType.indexOf(('_')) > -1) {
        assessmentType = assessmentType.replace('_', '-');
      }
  return <>        <Link fontSize="heading-m"
  href={`/assessments/${assessmentType}`}>{assessmentType}</Link>
  </>
}

export const LandingPage = () => {

  const [apiData, setApiData] = useState<ApiResponseState<ResultList<JobModel>>>({
    responseBody: {Results: []},
    error: null,
    loading: false
  });

  const {setNotifications} = useContext(NotificationContext);

  function loadLatestJobsFromApi() {
    setApiData({responseBody: {Results: []}, error: null, loading: true});
    get<ResultList<JobModel>>(`${apiPathJobs}`, {queryStringParameters: {'selection': 'latest'}}).then((result) => {
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
    loadLatestJobsFromApi();
  }, []);


  const cardDefinition: CardsProps.CardDefinition<JobModel> = {
    header: item => <HeaderComponent item={item}/>, //NOSONAR S6478: will be refactored in a feature release.
    sections: [
      {
        id: "JobStatus",
        header: "Job Status",
        content: item => item.JobStatus
      },
      {
        id: "FinishedAt",
        header: "Finished At",
        content: item => formattedDateTime(item.FinishedAt) || '-'
      },
      {
        id: "StartedBy",
        header: "Started By",
        content: item => item.StartedBy
      },
      {
        id: "JobId",
        header: "Job ID",
        content: item => <Link href={`/jobs/${item.AssessmentType}/${item.JobId}`}>{item.JobId}</Link> //NOSONAR S6478: will be refactored in a feature release.
      }
    ]
  };
  return (
    <ContentLayout
      header={
        <Header
          variant="h1"
          description="Account Assessment for AWS Organizations"
        >
          Welcome
        </Header>
      }
    >
      <div>
        <Cards
          cardDefinition={cardDefinition}
          cardsPerRow={[
            {cards: 1},
            {minWidth: 500, cards: 2}
          ]}
          items={apiData.responseBody?.Results || []}
          loading={apiData.loading}
          loadingText="Loading Assessments"
          empty={
            <Box textAlign="center" color="inherit">
              <b>No Assessments</b>
              <Box
                padding={{bottom: "s"}}
                variant="p"
                color="inherit"
              >
                No assessments have been started yet.
              </Box>
            </Box>
          }
          header={<Header>Most Recent Assessments</Header>}
        ></Cards>
      </div>
    </ContentLayout>
  );
}