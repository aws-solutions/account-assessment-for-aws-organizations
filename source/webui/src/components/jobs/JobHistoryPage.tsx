// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as React from "react";
import {useEffect} from "react";
import {JobModel} from "./JobModel";
import {jobHistoryColumns} from "./JobsDefinitions";
import {FullPageAssessmentResultTable} from "../../util/AssessmentResultTable";
import {Button} from "@cloudscape-design/components";
import {useDispatch, useSelector} from "react-redux";
import {ApiDataState, ApiDataStatus} from "../../store/types.ts";
import {fetchJobs} from "../../store/jobs-thunks.ts";

export const JobHistoryPage = () => {

  const dispatch = useDispatch<any>();

  const jobs = useSelector(
    ({jobs}: { jobs: ApiDataState<JobModel> }) => jobs,
  );

  // if jobs haven't been fetched from backend before, fetch them on page load
  useEffect(() => {
    if (jobs.status === ApiDataStatus.IDLE)
      dispatch(fetchJobs());
  }, []);

  const loading = jobs.status === ApiDataStatus.LOADING;
  const data = Object.values(jobs.entities) ?? [];
  return (
    <FullPageAssessmentResultTable
      title={"Job History"}
      actions={<>
        <Button
          iconName="refresh"
          onClick={() => dispatch(fetchJobs())}
          disabled={loading}>
          Refresh
        </Button>
      </>}
      data={data}
      loading={loading}
      columnDefinitions={jobHistoryColumns}
      defaultSorting={{
        sortingColumn: {sortingField: 'StartedAt'},
        isDescending: true
      }}
    ></FullPageAssessmentResultTable>
  );
}
