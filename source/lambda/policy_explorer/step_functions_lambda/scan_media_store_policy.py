# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_mediastore.type_defs import ContainerTypeDef, GetContainerPolicyOutputTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.media_store import MediaStore
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class MediaStorePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning Media Store Container Policies in {region}")
        media_store_client = MediaStore(self.account_id, region)
        media_store_container_names: list[model.MediaStoreContainerData] = self._get_media_store_container_names(
            media_store_client)
        media_store_names_policies: list[model.PolicyDetails] = self._get_media_store_data(
            media_store_container_names,
            media_store_client
        )
        media_store_policy_dynamodb_items = []
        for media_store_names_policy in media_store_names_policies:
            if media_store_names_policy.get('Policy'):
                media_store_policy_dynamodb_items.extend(
                    DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(media_store_names_policy))
        return media_store_policy_dynamodb_items

    def _get_media_store_container_names(self, media_store_client) -> list[model.MediaStoreContainerData]:
        container_objects: list[ContainerTypeDef] = media_store_client.list_containers()
        return list(self.denormalize_to_container_data(container_data) for container_data in
                    container_objects)

    @staticmethod
    def denormalize_to_container_data(container_data: ContainerTypeDef) -> model.MediaStoreContainerData:
        data: model.MediaStoreContainerData = {
            "Name": container_data['Name'],
            "Arn": container_data['ARN']
        }
        return data

    def _get_media_store_data(self, media_store_container_data: list[model.MediaStoreContainerData],
                              media_store_client) -> list[model.PolicyDetails]:
        container_policies = []
        for container in media_store_container_data:
            resource_arn = container['Arn']
            self.logger.info(resource_arn)
            policy_details = get_policy_details_from_arn(resource_arn)
            policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
            policy: GetContainerPolicyOutputTypeDef = media_store_client.get_container_policy(
                container['Name']
            )
            policy_details.update({'Policy': policy.get('Policy')})
            container_policies.append(policy_details)
        return container_policies
