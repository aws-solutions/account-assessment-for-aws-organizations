# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_schemas.type_defs import RegistrySummaryTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.eventbridge_schemas import EventBridgeSchemas
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn
    

class EventBridgeSchemasPolicy:
    
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']
        
    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)
    
    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning EventBridge Registry resource policies in {region}")
        eventbridge_schemas_client = EventBridgeSchemas(self.account_id, region)
        registries: list[RegistrySummaryTypeDef] = eventbridge_schemas_client.list_registries()
        registries_and_policies: list[model.PolicyAnalyzerRequest] = self._get_schemas_and_policies(registries, eventbridge_schemas_client)
        self.logger.debug(f"EventBridge Schema Registries and policies {registries_and_policies}")
        registries_and_policies_dynamodb_items = []
        for registry_and_policy in registries_and_policies:
            if registry_and_policy.get("Policy"):
                registries_and_policies_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(registry_and_policy))
        return registries_and_policies_dynamodb_items
    
    def _get_schemas_and_policies(self, registries: list[RegistrySummaryTypeDef], eventbridge_schemas_client: EventBridgeSchemas):
        return list(self._get_schema_resource_policy(registry, eventbridge_schemas_client) for registry in registries)
    
    @staticmethod
    def _get_schema_resource_policy(registry: RegistrySummaryTypeDef, eventbridge_schemas_client: EventBridgeSchemas) ->  model.PolicyDetails:
        resource_policy: str = eventbridge_schemas_client.get_resource_policy(registry.get('RegistryName'))
        resource_arn: str = registry.get('RegistryArn')
        policy_details = get_policy_details_from_arn(resource_arn)
        policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
        policy_details.update({'Policy': resource_policy})
        return policy_details
