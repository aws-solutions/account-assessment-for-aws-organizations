#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv

from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler
from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws_lambda_powertools import Logger
from mypy_boto3_mediastore.type_defs import ListContainersOutputTypeDef, GetContainerPolicyOutputTypeDef, \
    ContainerTypeDef


class MediaStore:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('mediastore', credentials=account_credentials, region=region)
        self.media_store_client = boto_session.get_client()

    @service_exception_handler
    def list_containers(self) -> list[ContainerTypeDef]:
        response: ListContainersOutputTypeDef = self.media_store_client.list_containers()

        containers = response.get('Containers', [])
        next_token = response.get('NextToken', None)

        while next_token is not None:
            self.logger.debug(f"NextToken Returned: {next_token})")
            response = self.media_store_client.list_containers(
                NextToken=next_token
            )
            self.logger.info("Extending CodeBuild Project List")
            containers.extend(response.get('Containers', []))
            next_token = response.get('NextToken', None)
        self.logger.debug(f"Container: {containers}")
        return containers

    @resource_not_found_exception_handler
    def get_container_policy(self, container_name: str) -> GetContainerPolicyOutputTypeDef:
        response = self.media_store_client.get_container_policy(
            ContainerName=container_name
        )
        self.logger.debug(f"Media Store Container Policy: {response}")
        return response

