// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as React from "react";
import {useEffect} from "react";
import {DelegatedAdminModel} from "./DelegatedAdminModel";
import {Button, SpaceBetween} from "@cloudscape-design/components";
import {JobModel} from "../jobs/JobModel";
import {
  delegatedAdminCsvAttributes,
  delegatedAdminCsvHeader,
  delegatedAdminDefinitions
} from "./DelegatedAdminDefinitions";
import {FullPageAssessmentResultTable} from "../../util/AssessmentResultTable";
import {useNavigate} from "react-router-dom";
import {useDispatch, useSelector} from "react-redux";
import {fetchDelegatedAdmins, startDelegatedAdminsScan} from "../../store/delegated-admin-thunks.ts";
import {ApiDataState, ApiDataStatus} from "../../store/types.ts";
import {downloadCSV} from "../policy-explorer/create-csv.ts";

export const DelegatedAdminPage = () => {

  const dispatch = useDispatch<any>();
  const navigate = useNavigate();

  const delegatedAdmins = useSelector(
    ({delegatedAdmins}: { delegatedAdmins: ApiDataState<DelegatedAdminModel> }) => delegatedAdmins,
  );

  // if DelegatedAdmins haven't been fetched from backend before, fetch them on page load
  useEffect(() => {
    if (delegatedAdmins.status === ApiDataStatus.IDLE)
      dispatch(fetchDelegatedAdmins());
  }, []);

  const startScan = () => {
    dispatch(startDelegatedAdminsScan()).then(
      ({payload}: { payload: JobModel }) => {
        if (payload)
          navigate(`/jobs/${payload.AssessmentType}/${payload.JobId}`)
      }
    )
  };

  const loading = delegatedAdmins.status === ApiDataStatus.LOADING;
  const data = Object.values(delegatedAdmins.entities) ?? [];
  return (
    <FullPageAssessmentResultTable
      title={"Delegated Admin Accounts"}
      data={data}
      loading={loading}
      columnDefinitions={delegatedAdminDefinitions}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={() => dispatch(fetchDelegatedAdmins())}
                  disabled={loading}>
            Refresh
          </Button>
          <Button variant={"primary"} loading={loading} onClick={startScan}>Start
            Scan</Button>
          <Button data-testid="download" variant="normal"
                  onClick={() => downloadCSV(data, 'delegated-admins', delegatedAdminCsvHeader, delegatedAdminCsvAttributes)}>
            Download Results
          </Button>
        </SpaceBetween>
      }
    ></FullPageAssessmentResultTable>
  );
}
