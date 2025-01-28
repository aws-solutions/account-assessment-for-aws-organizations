# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler
from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws_lambda_powertools import Logger
from mypy_boto3_redshift_serverless import ListSnapshotsPaginator
from mypy_boto3_redshift_serverless.type_defs import ListSnapshotsResponseTypeDef, SnapshotTypeDef, GetResourcePolicyResponseTypeDef, ResourcePolicyTypeDef

class RedshiftServerless:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region 
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__ }")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session: Boto3Session = Boto3Session('redshift-serverless', credentials=account_credentials, region=region)
        self.redshift_serverless_client = boto_session.get_client()
        
    @service_exception_handler
    def list_snapshots(self):
        response: ListSnapshotsResponseTypeDef = self.redshift_serverless_client.list_snapshots()
        snapshot_list: list[SnapshotTypeDef] = response.get('snapshots', [])
        next_token = response.get('nextToken', None)
        
        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token}")
            response = self.redshift_serverless_client.list_snapshots(
                nextToken=next_token
            )
            self.logger.info(f"Extending snapshot list")
            snapshot_list.extend(response.get('snapshots'), [])
            next_token = response.get('nextToken', None)
        self.logger.info(snapshot_list)
        return snapshot_list
    
    @resource_not_found_exception_handler
    def get_resource_policy(self, resource_arn: str) -> str:
        response: GetResourcePolicyResponseTypeDef = self.redshift_serverless_client.get_resource_policy(
            resourceArn=resource_arn
        )
        self.logger.debug(f"Resource Policy for {resource_arn}: {response}")
        self.logger.info(response.get('resourcePolicy').get('policy'))
        return response.get('resourcePolicy').get('policy')        