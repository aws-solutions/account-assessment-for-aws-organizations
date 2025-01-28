# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv

from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws_lambda_powertools import Logger
from mypy_boto3_efs.type_defs import FileSystemDescriptionTypeDef, DescribeFileSystemsResponseTypeDef
import policy_explorer.policy_explorer_model as model


class ElasticFileSystem:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('efs', credentials=account_credentials, region=region)
        self.efs_client = boto_session.get_client()

    @service_exception_handler
    def describe_file_systems(self) -> list[FileSystemDescriptionTypeDef]:
        response: DescribeFileSystemsResponseTypeDef = self.efs_client.describe_file_systems()
        file_systems = response.get('FileSystems', [])
        marker = response.get('NextMarker', None)

        while marker is not None:
            self.logger.debug(f"Marker Returned: {marker})")
            response = self.efs_client.describe_file_systems(
                Marker=marker
            )
            self.logger.info("Extending File Systems List")
            file_systems.extend(response.get('FileSystems', []))
            marker = response.get('NextMarker', None)
        self.logger.debug(f"Elastic File Systems: {file_systems})")
        return file_systems

    @resource_not_found_exception_handler
    def describe_file_system_policy(self, file_system_id) -> model.DescribeFileSystemPolicyResponse:
        response = self.efs_client.describe_file_system_policy(
            FileSystemId=file_system_id
        )
        self.logger.debug(f"File System Policy: {response}")
        return response

