// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {ContentLayout, Header, SpaceBetween} from "@cloudscape-design/components"
import {SearchForm} from "./SearchForm"
import {PolicyExplorerTable} from "./PolicyExplorerTable"
import {useEffect, useState} from "react";
import {TableState} from "../../util/AssessmentResultTable.tsx";
import {contentDisplayItems} from "./PolicyExplorerDefinitions.tsx";
import {useDispatch, useSelector} from "react-redux";
import {ApiDataState, ApiDataStatus} from "../../store/types.ts";
import {JobModel} from "../jobs/JobModel.ts";
import {fetchJobs} from "../../store/jobs-thunks.ts";
import {format} from "date-fns";

export const PolicyExplorerPage = () => {

  const initialTableState = {
    header: "Policies",
    start: 1,
    itemsPerPage: 20,
    contentDisplayOption: contentDisplayItems
  };
  const [tableState, setTableState] = useState<TableState>(initialTableState);

  const dispatch = useDispatch<any>();
  // if jobs haven't been fetched from backend before, fetch them on page load
  useEffect(() => {
    if (jobsData.status === ApiDataStatus.IDLE)
      dispatch(fetchJobs());
  }, []);

  const jobsData = useSelector(
      ({jobs}: { jobs: ApiDataState<JobModel> }) => jobs,
  );
  const jobModels = Object.values(jobsData.entities).filter(job => job.AssessmentType === 'POLICY_EXPLORER');
  const latestJob = jobModels.reduce((maxJob: JobModel | null, currentJob: JobModel) => {
    if (!maxJob || currentJob.StartedAt > maxJob?.StartedAt) {
      return currentJob;
    }
    return maxJob;
  }, null);

  let statusMessage = "";
  switch (latestJob?.JobStatus) {
    case "SUCCEEDED":
      statusMessage = `The policies in your organization were successfully scanned at ${(format(latestJob.StartedAt, "yyyy-MM-dd HH-mm"))}.`
      break;
    case "SUCCEEDED_WITH_FAILED_TASKS":
      statusMessage = `The most recent scan succeeded with partial failures. The collected policy data is incomplete. Visit the Job History page to understand which resources could not be scanned.`
      break;
    default:
      statusMessage = `No policy scan has been completed yet. There is no policy data available. Scans will run on a nightly schedule.`
  }


  return (
    <ContentLayout
      header={
        <Header variant="h1"
                description={statusMessage}
        >Policy Explorer</Header>
      }
    >
      <SpaceBetween size={"l"}>
        <SearchForm
          resetTableState={() => setTableState(initialTableState)}
        ></SearchForm>
        <PolicyExplorerTable
          tableState={tableState}
          setTableState={setTableState}
        ></PolicyExplorerTable>
      </SpaceBetween>
    </ContentLayout>
  )
}