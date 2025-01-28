// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

export enum PolicyTypes {
    "IDENTITY_BASED_POLICIES" = "IdentityBasedPolicy",
    "RESOURCE_BASED_POLICIES" = "ResourceBasedPolicy",
    "SERVICE_CONTROL_POLICIES" = "ServiceControlPolicy"
}

export type PolicySearchModel = {
    policyType: PolicyTypes, 
    filters: FiltersForPolicySearch,
}

export type FiltersForPolicySearch = {
    action?: string,
    notAction?: string,
    principal?: string,
    notPrincipal?: string,
    condition?: string,
    region?: string,
    resource?: string,
    notResource?: string,
    effect?: 'Allow' | 'Deny'
}

export type QueryStringParams = FiltersForPolicySearch;

export type PolicyModel = {
    PartitionKey: string,
    AccountId: string,
    Effect: string,
    Resource: string,
    Region: string,
    Service: string,
    ResourceIdentifier: string,
    Policy: string,
    Action: string,
    NotResource: string,
    NotAction: string,
    JobId: string,
    SortKey: string,
}
