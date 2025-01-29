// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {Box, Cards, CardsProps, ContentLayout} from "@cloudscape-design/components";
import * as React from "react";
import {useEffect} from "react";
import {JobModel} from "../jobs/JobModel";
import Header from "@cloudscape-design/components/header";
import {formattedDateTime} from "../../util/Formatter";
import {useDispatch, useSelector} from "react-redux";
import {RouterLink} from "../navigation/RouterLink.tsx";
import {ApiDataState, ApiDataStatus} from "../../store/types.ts";
import {fetchJobs} from "../../store/jobs-thunks.ts";

function HeaderComponent({item}: {
  item: JobModel
}) {
  let assessmentType = item.AssessmentType;
  while (assessmentType.indexOf(('_')) > -1) {
    assessmentType = assessmentType.replace('_', '-');
  }
  return <>
    <RouterLink fontSize="heading-m" href={`/${assessmentType}`}>{assessmentType}</RouterLink>
  </>
}

export const LandingPage = () => {

  const dispatch = useDispatch<any>();

  const jobs = useSelector(
    ({jobs}: { jobs: ApiDataState<JobModel> }) => jobs,
  );
  const mostRecentJobs = getMostRecentPerAssessmentType(Object.values(jobs.entities));

  // if jobs haven't been fetched from backend before, fetch them on page load
  useEffect(() => {
    if (jobs.status === ApiDataStatus.IDLE)
      dispatch(fetchJobs());
  }, []);

  const loading = jobs.status === ApiDataStatus.LOADING;
  const cardDefinition: CardsProps.CardDefinition<JobModel> = {
    header: item => <HeaderComponent item={item}/>,
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
        content: item => <RouterLink href={`/jobs/${item.AssessmentType}/${item.JobId}`}>{item.JobId}</RouterLink>
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
          items={mostRecentJobs}
          loading={loading}
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

function getMostRecentPerAssessmentType(jobs: Array<JobModel>) {
  const reducedJobs = jobs.reduce((acc: { [key: string]: JobModel }, job: JobModel) => {
    const existingJob = acc[job.AssessmentType];
    if (!existingJob || existingJob.StartedAt < job.StartedAt) {
      acc[job.AssessmentType] = job;
    }
    return acc;
  }, {});

  return Object.values(reducedJobs);
}
