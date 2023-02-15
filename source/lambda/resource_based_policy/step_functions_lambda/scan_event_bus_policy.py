# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_events.type_defs import EventBusTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.events import Events
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class EventBusPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Event Bus Policies in {region}")
        events_client = Events(self.account_id, region)
        events_names_policies: list[model.PolicyAnalyzerRequest] = self._get_events_data(events_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(events_names_policies)
        events_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return events_resources_for_region

    def _get_events_data(self, events_client) -> list[model.PolicyAnalyzerRequest]:
        events_objects: list[EventBusTypeDef] = events_client.list_event_buses()
        return list(self.denormalize_to_events_data(events_data) for events_data in events_objects)

    @staticmethod
    def denormalize_to_events_data(events_data: EventBusTypeDef) -> model.PolicyAnalyzerRequest:
        if events_data.get('Policy'):
            return DenormalizePolicyAnalyzerRequest().model(
                events_data['Name'],
                events_data['Policy']
            )
