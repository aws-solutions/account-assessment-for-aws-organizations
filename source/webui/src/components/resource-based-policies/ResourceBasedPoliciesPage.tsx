// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as React from "react";
import {useEffect} from "react";
import {Button, SpaceBetween} from "@cloudscape-design/components";
import {
  resourceBasedPoliciesCsvAttributes,
  resourceBasedPoliciesCsvHeader,
  resourceBasedPolicyColumns
} from "./ResourceBasedPoliciesDefinitions";
import {FullPageAssessmentResultTable} from "../../util/AssessmentResultTable";
import {ResourceBasedPolicyModel} from "./ResourceBasedPolicyModel";
import {useDispatch, useSelector} from "react-redux";
import {ApiDataState, ApiDataStatus} from "../../store/types.ts";
import {fetchResourceBasedPolicies} from "../../store/resource-based-policies-thunks.ts";
import {downloadCSV} from "../policy-explorer/create-csv.ts";
import {useNavigate} from "react-router-dom";
import {PolicyTypes} from "../policy-explorer/PolicyExplorerModel.tsx";

export const ResourceBasedPoliciesPage = () => {

  const dispatch = useDispatch<any>();
  const navigate = useNavigate();

  const resourceBasedPoliciesData = useSelector(
    ({resourceBasedPolicies}: {
      resourceBasedPolicies: ApiDataState<ResourceBasedPolicyModel>
    }) => resourceBasedPolicies,
  );

  // if ResourceBasedPolicies haven't been fetched from backend before, fetch them on page load
  useEffect(() => {
    if (resourceBasedPoliciesData.status === ApiDataStatus.IDLE)
      dispatch(fetchResourceBasedPolicies());
  }, []);

  const loading = resourceBasedPoliciesData.status === ApiDataStatus.LOADING;
  const data = Object.values(resourceBasedPoliciesData.entities) || [];

  function navigateToPolicyExplorer() {
    navigate(`/policy-explorer?policyType=${PolicyTypes.RESOURCE_BASED_POLICIES}`)
  }

  return (
    <FullPageAssessmentResultTable
      title={"Resource-Based Policies"}
      description={"Legacy feature. This page displays results of policy scans from Account Assessment v1.0.x (before v1.1.0). For new data, use the Policy Explorer page to browse the results of the periodical scan."}
      data={data}
      loading={loading}
      columnDefinitions={resourceBasedPolicyColumns}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button iconName="refresh" onClick={() => dispatch(fetchResourceBasedPolicies())} disabled={loading}>
            Refresh
          </Button>
          <Button variant={"primary"} onClick={navigateToPolicyExplorer}>
            Policy Explorer
          </Button>
          <Button data-testid="download" variant="normal"
                  onClick={() => downloadCSV(data, 'resource-based-policies', resourceBasedPoliciesCsvHeader, resourceBasedPoliciesCsvAttributes)}>
            Download Results
          </Button>
        </SpaceBetween>
      }
    ></FullPageAssessmentResultTable>
  );

}
