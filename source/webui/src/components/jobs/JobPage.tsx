// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as React from "react";
import {useEffect, useState} from "react";
import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import {
  Box,
  Button,
  ContentLayout,
  Grid,
  Modal,
  SpaceBetween,
  Spinner,
  TableProps
} from "@cloudscape-design/components";
import {useNavigate, useParams} from "react-router-dom";
import {deleteItem} from "../../util/ApiClient";
import {JobDetails} from "./JobModel";
import {delegatedAdminColumnsForJob} from "../delegated-admin/DelegatedAdminDefinitions";
import {ContainerAssessmentResultTable} from "../../util/AssessmentResultTable";
import {trustedAccessColumnsForJob} from "../trusted-access/TrustedAccessDefinitions";
import {apiPathJobs, taskFailureColumns} from "./JobsDefinitions";
import {resourceBasedPolicyColumnsForJob} from "../resource-based-policies/ResourceBasedPoliciesDefinitions";
import {useDispatch, useSelector} from "react-redux";
import {addNotification} from "../../store/notifications-slice.ts";
import {v4} from "uuid";
import {fetchJobDetails} from "../../store/job-details-thunks.ts";
import {RootState} from "../../store/store.ts";
import {ApiDataStatus} from "../../store/types.ts";
import {selectJobDetailsById} from "../../store/job-details-slice.ts";

export const JobPage = () => {

  const {assessmentType, id} = useParams();
  const dispatch = useDispatch<any>();

  let title = "Findings";
  let columnDefinitions: TableProps.ColumnDefinition<any>[] = [];
  switch (assessmentType) {
    case 'DELEGATED_ADMIN': {
      title = "Delegated Admin Accounts";
      columnDefinitions = delegatedAdminColumnsForJob;
      break;
    }
    case 'TRUSTED_ACCESS': {
      title = "Trusted Access";
      columnDefinitions = trustedAccessColumnsForJob;
      break;
    }
    case 'RESOURCE_BASED_POLICY': {
      title = "Resource-Based Policies";
      columnDefinitions = resourceBasedPolicyColumnsForJob;
      break;
    }
  }

  const [modalVisible, setModalVisible] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const navigate = useNavigate();

  const job: JobDetails | null = id ? useSelector((state: RootState) => selectJobDetailsById(state, `${assessmentType}#${id}`)) : null;
  const status = useSelector(
    ({jobDetails}: RootState) => jobDetails,
  ).status;

  function loadJob() {
    if (assessmentType && id)
      dispatch(fetchJobDetails({assessmentType, jobId: id}))
  }

  useEffect(() => {
    loadJob();
  }, []);

  const loading = status === ApiDataStatus.LOADING;
  return (
    <ContentLayout
      header={
        <Header
          variant="h1"
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Button iconName="refresh" onClick={loadJob} disabled={loading}>
                Refresh
              </Button>
            </SpaceBetween>
          }
        >
          Job {job?.Job?.JobId}
        </Header>
      }
    >
      <SpaceBetween size={"m"}>
        <Container
          header={
            <Header variant="h2">
              Job Details
            </Header>
          }
          data-testid={'job-details-container'}
        >
          {loading ? <><Spinner/>Loading resources</> : job ?
            <Grid
              gridDefinition={[{colspan: 4}, {colspan: 4}, {colspan: 4}, {colspan: 4}, {colspan: 4}]}
            >
              <div>
                <div><strong>Status</strong></div>
                <div>{job.Job.JobStatus}</div>
              </div>
              <div>
                <div><strong>Assessment Type</strong></div>
                <div>{job.Job.AssessmentType}</div>
              </div>
              <div>
                <div><strong>Started By</strong></div>
                <div>{job.Job.StartedBy}</div>
              </div>
              <div>
                <div><strong>Started At</strong></div>
                <div>{job.Job.StartedAt}</div>
              </div>
              <div>
                <div><strong>Finished At</strong></div>
                <div>{job.Job.FinishedAt}</div>
              </div>
            </Grid>
            : <></>}
        </Container>
        {columnDefinitions.length ?
          <div title={'FindingsTable'}>
            <ContainerAssessmentResultTable
              title={title}
              actions={<></>}
              data={job?.Findings || []}
              loading={loading}
              columnDefinitions={columnDefinitions}
            ></ContainerAssessmentResultTable>
          </div>
          : <></>
        }
        {(job?.TaskFailures?.length) ?
          <div title={'FailuresTable'}>
            <ContainerAssessmentResultTable
              title={'Failed Tasks During Scan'}
              actions={<></>}
              data={job?.TaskFailures || []}
              loading={loading}
              columnDefinitions={taskFailureColumns}
            ></ContainerAssessmentResultTable>
          </div> : <></>}
      </SpaceBetween>
    </ContentLayout>
  );
}