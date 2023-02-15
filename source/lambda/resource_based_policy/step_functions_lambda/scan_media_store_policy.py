# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_mediastore.type_defs import ContainerTypeDef, GetContainerPolicyOutputTypeDef

import resource_based_policy.resource_based_policy_model as model
from aws.services.media_store import MediaStore
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.step_functions_lambda.utils import DenormalizeResourceBasedPolicyResponse, \
    DenormalizePolicyAnalyzerRequest, scan_regions


class MediaStorePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Media Store Container Policies in {region}")
        media_store_client = MediaStore(self.account_id, region)
        media_store_container_names: list[model.MediaStoreContainerData] = self._get_media_store_container_names(
            media_store_client)
        media_store_names_policies: list[model.PolicyAnalyzerRequest] = self._get_media_store_data(
            media_store_container_names,
            media_store_client
        )
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(media_store_names_policies)
        media_store_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return media_store_resources_for_region

    def _get_media_store_container_names(self, media_store_client) -> list[model.MediaStoreContainerData]:
        container_objects: list[ContainerTypeDef] = media_store_client.list_containers()
        return list(self.denormalize_to_container_data(container_data) for container_data in
                    container_objects)

    @staticmethod
    def denormalize_to_container_data(container_data: ContainerTypeDef) -> model.MediaStoreContainerData:
        data: model.MediaStoreContainerData = {
            "Name": container_data['Name']
        }
        return data

    def _get_media_store_data(self, media_store_container_data: list[model.MediaStoreContainerData],
                              media_store_client) -> list[model.PolicyAnalyzerRequest]:
        container_policies = []
        for container in media_store_container_data:
            self.logger.debug(f"Getting Policy for {container}")
            policy: GetContainerPolicyOutputTypeDef = media_store_client.get_container_policy(
                container['Name']
            )
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    container['Name'],
                    policy['Policy']
                )
                container_policies.append(policy_object)
        return container_policies
