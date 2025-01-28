# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_events.type_defs import EventBusTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.events import Events
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class EventBusPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning Event Bus Policies in {region}")
        events_client = Events(self.account_id, region)
        events_bus_policies: list[model.PolicyDetails] = self._get_events_data(events_client)
        event_bus_policy_dynamodb_items = []
        for event_bus_policy in events_bus_policies:
            if event_bus_policy.get("Policy"):
                event_bus_policy_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(event_bus_policy))

        return event_bus_policy_dynamodb_items

    def _get_events_data(self, events_client) -> list[model.PolicyDetails]:
        events_objects: list[EventBusTypeDef] = events_client.list_event_buses()
        return list(self.denormalize_to_events_data(events_data) for events_data in events_objects)

    @staticmethod
    def denormalize_to_events_data(events_data: EventBusTypeDef) -> model.PolicyDetails:
        resource_arn = events_data.get('Arn')
        policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
        policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
        policy_details.update({'Policy': events_data.get('Policy')})
        return policy_details
