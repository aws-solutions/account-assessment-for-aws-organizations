# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_opensearch.type_defs import DomainInfoTypeDef, DomainStatusTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.open_search import OpenSearch
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class OpenSearchDomainPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning OpenSearch Domain Policies in {region}")
        opensearch_client = OpenSearch(self.account_id, region)
        opensearch_domain_names: model.OpenSearchData = self._get_opensearch_domain_names(opensearch_client)
        opensearch_domain_policies = self._get_opensearch_domain_policies(opensearch_domain_names,
                                                                          opensearch_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(opensearch_domain_policies)
        opensearch_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return opensearch_resources_for_region

    def _get_opensearch_domain_names(self, opensearch_client) -> model.OpenSearchData:
        domain_objects: list[DomainInfoTypeDef] = opensearch_client.list_domain_names()
        return self.denormalize_to_opensearch_data(domain_objects)

    @staticmethod
    def denormalize_to_opensearch_data(domain_data: list[DomainInfoTypeDef]) -> model.OpenSearchData:
        domain_names = []
        for domain in domain_data:
            domain_names.append(domain['DomainName'])
        data: model.OpenSearchData = {
            "DomainNames": domain_names
        }
        return data

    @staticmethod
    def _get_opensearch_domain_policies(
            opensearch_data: model.OpenSearchData,
            opensearch_client) -> list[model.PolicyAnalyzerRequest]:
        opensearch_policies = []
        if opensearch_data.get('DomainNames'):
            domain_policies: list[DomainStatusTypeDef] = opensearch_client.describe_domains(
                opensearch_data['DomainNames']
            )
            for policy in domain_policies:
                if policy.get('AccessPolicies'):
                    policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                        policy['DomainName'],
                        policy['AccessPolicies']
                    )
                    opensearch_policies.append(policy_object)
        return opensearch_policies
