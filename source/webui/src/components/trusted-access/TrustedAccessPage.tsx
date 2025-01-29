// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as React from "react";
import {useEffect} from "react";
import {TrustedAccessModel} from "./TrustedAccessModel";
import {Button, SpaceBetween} from "@cloudscape-design/components";
import {JobModel} from "../jobs/JobModel";
import {FullPageAssessmentResultTable} from "../../util/AssessmentResultTable";
import {trustedAccessColumns, trustedAccessCsvAttributes, trustedAccessCsvHeader} from "./TrustedAccessDefinitions";
import {useNavigate} from "react-router-dom";
import {useDispatch, useSelector} from "react-redux";
import {ApiDataState, ApiDataStatus} from "../../store/types.ts";
import {fetchTrustedAccess, startTrustedAccessScan} from "../../store/trusted-access-thunks.ts";
import {downloadCSV} from "../policy-explorer/create-csv.ts";

export const TrustedAccessPage = () => {

  const dispatch = useDispatch<any>();
  const navigate = useNavigate();

  const trustedAccessData = useSelector(
    ({trustedAccess}: { trustedAccess: ApiDataState<TrustedAccessModel> }) => trustedAccess,
  );

  // if DelegatedAdmins haven't been fetched from backend before, fetch them on page load
  useEffect(() => {
    if (trustedAccessData.status === ApiDataStatus.IDLE)
      dispatch(fetchTrustedAccess());
  }, []);

  const startScan = () => {
    dispatch(startTrustedAccessScan()).then(
      ({payload}: { payload: JobModel }) => {
        if (payload)
          navigate(`/jobs/${payload.AssessmentType}/${payload.JobId}`)
      }
    )
  };

  const loading = trustedAccessData.status === ApiDataStatus.LOADING;
  const data = Object.values(trustedAccessData.entities) || [];
  return (
    <FullPageAssessmentResultTable
      title={"Trusted Access"}
      data={data}
      loading={loading}
      columnDefinitions={trustedAccessColumns}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={() => dispatch(fetchTrustedAccess())}
                  disabled={loading}>
            Refresh
          </Button>
          <Button variant={"primary"} loading={loading} onClick={startScan}>Start
            Scan</Button>
          <Button data-testid="download" variant="normal"
                  onClick={() => downloadCSV(data, 'trusted-access', trustedAccessCsvHeader, trustedAccessCsvAttributes)}>
            Download Results
          </Button>
        </SpaceBetween>
      }
    ></FullPageAssessmentResultTable>
  );
}
