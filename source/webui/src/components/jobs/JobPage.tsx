// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as React from "react";
import {useContext, useEffect, useState} from "react";
import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import {Box, Button, ContentLayout, Grid, Modal, SpaceBetween, TableProps} from "@cloudscape-design/components";
import {useNavigate, useParams} from "react-router-dom";
import {ApiResponseState, deleteItem, get} from "../../util/ApiClient";
import {JobDetails} from "./JobModel";
import {NotificationContext} from "../../contexts/NotificationContext";
import {delegatedAdminColumnsForJob} from "../delegated-admin/DelegatedAdminDefinitions";
import {ContainerAssessmentResultTable} from "../../util/AssessmentResultTable";
import {trustedAccessColumnsForJob} from "../trusted-access/TrustedAccessDefinitions";
import {apiPathJobs, taskFailureColumns} from "./JobsDefinitions";
import {resourceBasedPolicyColumnsForJob} from "../resource-based-policies/ResourceBasedPoliciesDefinitions";

export const JobPage = () => {

  const {assessmentType, id} = useParams();

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

  const [apiData, setApiData] = useState<ApiResponseState<JobDetails | null>>({
    responseBody: null,
    error: null,
    loading: true
  });

  const {setNotifications} = useContext(NotificationContext);
  const [modalVisible, setModalVisible] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const navigate = useNavigate();

  function loadJob() {
    get<JobDetails>(`${apiPathJobs}/${assessmentType}/${id}`).then(async (result: ApiResponseState<JobDetails>) => {
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
    setApiData({responseBody: null, error: null, loading: true});
    loadJob();
  }, []);

  function deleteJob() {
    setNotifications([]);
    setDeleting(true);
    setModalVisible(false);

    deleteItem<void>(`${apiPathJobs}/${assessmentType}/${id}`).then((state) => {
        if (state.error) {
          setNotifications([{
            header: 'Error',
            content: 'Job could not be deleted',
            type: 'error',
            dismissible: true,
            onDismiss: () => setNotifications([])
          }]);
          setDeleting(false);
        } else {
          setNotifications([{
            header: 'Job deleted',
            content: `Job with JobId ${id} was deleted successfully.`,
          }]);
          navigate('/jobs');
          setDeleting(false);
        }
      }
    );
  }

  const job = apiData.responseBody?.Job;
  return (
    <ContentLayout
      header={
        <Header
          variant="h1"
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Button iconName="refresh" onClick={loadJob} disabled={apiData.loading}>
                Refresh
              </Button>
              <Button variant="primary" loading={deleting}
                      onClick={() => setModalVisible(true)}>Delete</Button>
            </SpaceBetween>
          }
        >
          Job {job?.JobId}
        </Header>
      }
    >
      <SpaceBetween size={"m"}>

        <Modal
          visible={modalVisible}
          closeAriaLabel="Close modal"
          footer={
            <Box float="right">
              <SpaceBetween direction="horizontal" size="xs">
                <Button variant="link" onClick={() => setModalVisible(false)}>Cancel</Button>
                <Button variant="primary" onClick={deleteJob}>Ok</Button>
              </SpaceBetween>
            </Box>
          }
          header="Delete Job">
          Do you want to delete this job and all associated findings?
        </Modal>

        <Container
          header={
            <Header variant="h2">
              Job Details
            </Header>
          }
        >{job &&
          <Grid
            gridDefinition={[{colspan: 4}, {colspan: 4}, {colspan: 4}, {colspan: 4}]}
          >
            <div>
              <div><strong>Status</strong></div>
              <div>{job.JobStatus}</div>
            </div>
            <div>
              <div><strong>Assessment Type</strong></div>
              <div>{job.AssessmentType}</div>
            </div>
            <div>
              <div><strong>Started By</strong></div>
              <div>{job.StartedBy}</div>
            </div>
            <div>
              <div><strong>Started At</strong></div>
              <div>{job.StartedAt}</div>
            </div>
            <div>
              <div><strong>Finished At</strong></div>
              <div>{job.FinishedAt}</div>
            </div>
          </Grid>
        }
        </Container>
        <div title={'FindingsTable'}>
          <ContainerAssessmentResultTable
            title={title}
            actions={<></>}
            data={apiData?.responseBody?.Findings || []}
            loading={apiData.loading}
            columnDefinitions={columnDefinitions}
          ></ContainerAssessmentResultTable>
        </div>

        {(apiData?.responseBody?.TaskFailures?.length) ?
          <div title={'FailuresTable'}>
            <ContainerAssessmentResultTable
              title={'Failed Tasks During Scan'}
              actions={<></>}
              data={apiData?.responseBody?.TaskFailures || []}
              loading={apiData.loading}
              columnDefinitions={taskFailureColumns}
            ></ContainerAssessmentResultTable>
          </div> : <></>}
      </SpaceBetween>
    </ContentLayout>
  );
}