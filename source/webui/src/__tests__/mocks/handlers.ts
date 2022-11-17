// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {rest} from 'msw'
import {JobDetails, JobTaskFailure} from "../../components/jobs/JobModel";
import {randomUUID} from "crypto";
import {apiPathResourceBasedPolicies} from "../../components/resource-based-policies/ResourceBasedPoliciesDefinitions";
import {apiPathDelegatedAdmins} from "../../components/delegated-admin/DelegatedAdminDefinitions";
import {apiPathTrustedAccess} from "../../components/trusted-access/TrustedAccessDefinitions";
import {DelegatedAdminModel} from "../../components/delegated-admin/DelegatedAdminModel";
import {TrustedAccessModel} from "../../components/trusted-access/TrustedAccessModel";
import {ResourceBasedPolicyModel} from "../../components/resource-based-policies/ResourceBasedPolicyModel";
import {delegatedAdminItems} from "../DelegatedAdminPage.test";


export const newJobId = randomUUID();

export function newJob(assessmentType?: string, jobId?: string) {
  return {
    AssessmentType: assessmentType || "DELEGATED_ADMIN",
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
export const handlers = [

  rest.get('/jobs/:assessmentType/:id', (request, response, context) => {
    return response(
      context.status(200),
      context.json(newJobDetails())
    )
  }),

  rest.delete('/jobs/:assessmentType/:id', (request, response, context) => {
    return response(
      context.status(204)
    )
  }),


  rest.get('/jobs', (request, response, context) => {
    return response(
      context.status(200),
      context.json({Results: []}),
    )
  }),

  rest.post(apiPathDelegatedAdmins, (request, response, context) => {
    return response(
      context.status(200),
      context.json(newJob())
    )
  }),

  rest.get(apiPathDelegatedAdmins, (request, response, context) => {
    return response(
      context.status(200),
      context.json({Results: []}),
    )
  }),

  rest.post(apiPathTrustedAccess, (request, response, context) => {
    return response(
      context.status(200),
      context.json(newJob())
    )
  }),

  rest.get(apiPathTrustedAccess, (request, response, context) => {
    return response(
      context.status(200),
      context.json({Results: []}),
    )
  }),

  rest.post(apiPathResourceBasedPolicies, (request, response, context) => {
    const activeJob = newJob('RESOURCE_BASED_POLICY');
    activeJob.JobStatus = 'ACTIVE';
    return response(
      context.status(200),
      context.json(activeJob)
    )
  }),

  rest.get(apiPathResourceBasedPolicies, (request, response, context) => {
    return response(
      context.status(200),
      context.json({Results: []}),
    )
  }),

  rest.get('scan-configs', (request, response, context) => {

    return response(
      context.status(200),
      context.json(sampleSelectionOptions),
    )
  }),
]