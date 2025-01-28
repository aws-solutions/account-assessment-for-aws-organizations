// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {delay, http, HttpResponse} from 'msw';
import {JobDetails, JobTaskFailure} from "../../components/jobs/JobModel";
import {apiPathResourceBasedPolicies} from "../../components/resource-based-policies/ResourceBasedPoliciesDefinitions";
import {apiPathDelegatedAdmins} from "../../components/delegated-admin/DelegatedAdminDefinitions";
import {apiPathTrustedAccess} from "../../components/trusted-access/TrustedAccessDefinitions";
import {DelegatedAdminModel} from "../../components/delegated-admin/DelegatedAdminModel";
import {TrustedAccessModel} from "../../components/trusted-access/TrustedAccessModel";
import {ResourceBasedPolicyModel} from "../../components/resource-based-policies/ResourceBasedPolicyModel";
import {delegatedAdminItems} from "../DelegatedAdminPage.test";
import {v4} from "uuid";

/**
 * Return a 200 OK http response with the given payload.
 * Delays the response by 200ms to simulate realistic latency and allow
 * to test a loading spinner etc on the UI.
 */
export const ok = async (payload: object | object[], delayMilliseconds: number = 200) => {
  await delay(delayMilliseconds);
  return HttpResponse.json(payload, {
    status: 200,
    headers: [['Access-Control-Allow-Origin', '*']],
  });
};
export const noContent = async (delayMilliseconds: number = 200) => {
  await delay(delayMilliseconds);
  return HttpResponse.json(undefined, {
    status: 204,
    headers: [['Access-Control-Allow-Origin', '*']],
  });
};
export const badRequest = async (payload: object | object[], delayMilliseconds: number = 200) => {
  await delay(delayMilliseconds);
  return HttpResponse.json(payload, {
    status: 400,
    headers: [['Access-Control-Allow-Origin', '*']],
  });
};

export const newJobId = v4();

export function newJob(assessmentType?: string, jobId?: string) {
  const type = assessmentType || "DELEGATED_ADMIN";
  return {
    SortKey: `${type}#${jobId ?? v4()}`,
    AssessmentType: type,
    JobId: jobId || newJobId,
    JobStatus: 'SUCCEEDED',
    StartedAt: new Date().toISOString(),
    StartedBy: 'John.Doe@example.com'
  };
}

export function newJobDetails(
  assessmentType?: string,
  jobId?: string,
  findings?: Array<DelegatedAdminModel | TrustedAccessModel | ResourceBasedPolicyModel>,
  taskFailures?: Array<JobTaskFailure>,
): JobDetails {
  return {
    Job: newJob(assessmentType, jobId),
    TaskFailures: taskFailures || [],
    Findings: findings || delegatedAdminItems
  } as JobDetails;
}

export function newTaskFailure(
  assessmentType?: string, jobId?: string
): JobTaskFailure {
  return {
    AssessmentType: assessmentType || "DELEGATED_ADMIN",
    JobId: jobId || newJobId,
    ServiceName: 'foo',
    AccountId: '111122223333',
    Region: 'us-east-1',
    FailedAt: new Date().toISOString(),
    Error: 'This is an error description.'
  }
}

export const sampleSelectionOptions = {
  "SavedConfigurations": [{
    "ExpiresAt": 1671743792,
    "AccountIds": ["111222333"],
    "Regions": ["us-east-1", "us-east-2", "us-west-1", "us-west-2"],
    "ServiceNames": ["apigateway"],
    "PartitionKey": "ScanConfigurations",
    "SortKey": "US",
    "ConfigurationName": "Sample-Config-US"
  }],
  "SupportedServices": [{
    "ServiceName": "apigateway",
    "ServicePrincipal": "apigateway.amazonaws.com",
    "FriendlyName": "Amazon API Gateway"
  }, {
    "ServiceName": "s3",
    "ServicePrincipal": "s3.amazonaws.com",
    "FriendlyName": "Amazon Simple Storage Service (Amazon S3)"
  }, {
    "ServiceName": "s3",
    "ServicePrincipal": "s3.amazonaws.com",
    "FriendlyName": "Amazon Simple Storage Service (Amazon S3)"
  }],
  "SupportedRegions": [{"Region": "us-east-1", "RegionName": "US East (N. Virginia)"}, {
    "Region": "us-east-2",
    "RegionName": "US East (Ohio)"
  }, {"Region": "us-west-1", "RegionName": "US West (N. California)"}, {
    "Region": "us-west-2",
    "RegionName": "US West (Oregon)"
  }]
};

// Default http responses for all tests. can be overwritten by individual tests with server.use(...)
export const handlers = (apiUrl: string) => [

  http.get(apiUrl + '/jobs/:assessmentType/:id', () => {
    return ok(newJobDetails())
  }),

  http.delete(apiUrl + '/jobs/:assessmentType/:id', () => {
    return noContent()
  }),


  http.get(apiUrl + '/jobs', () => {
    return ok({Results: []}
    )
  }),

  http.post(apiUrl + apiPathDelegatedAdmins, () => {
    return ok(newJob()
    )
  }),

  http.get(apiUrl + apiPathDelegatedAdmins, () => {
    return ok({Results: []}
    )
  }),

  http.post(apiUrl + apiPathTrustedAccess, () => {
    return ok(newJob()
    )
  }),

  http.get(apiUrl + apiPathTrustedAccess, () => {
    return ok({Results: []}
    )
  }),

  http.get(apiUrl + apiPathResourceBasedPolicies, () => {
    return ok({Results: []},)
  }),

]