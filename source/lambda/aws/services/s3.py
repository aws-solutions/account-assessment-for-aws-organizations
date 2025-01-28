# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from os import getenv
from typing import Dict

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError
from mypy_boto3_glacier.type_defs import DescribeVaultOutputTypeDef, VaultAccessPolicyTypeDef, ListVaultsOutputTypeDef
from mypy_boto3_s3.type_defs import GetBucketPolicyOutputTypeDef, ListBucketsOutputTypeDef

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws.utils.exceptions import resource_not_found_exception_handler, service_exception_handler


class S3:
    def __init__(self, account_id=None, region=getenv('AWS_REGION')):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        role_name = getenv('SPOKE_ROLE_NAME')
        if account_id:
            self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__} "
                              f"in region: {region}")
            account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
            boto_session = Boto3Session('s3', credentials=account_credentials, region=region)
        else:
            boto_session = Boto3Session('s3')
        self.s3_client = boto_session.get_client()

    @service_exception_handler
    def list_buckets(self) -> ListBucketsOutputTypeDef:
        response: ListBucketsOutputTypeDef = self.s3_client.list_buckets()
        self.logger.debug(f"Buckets: {response}")
        return response  # returns bucket information in all the regions

    @service_exception_handler
    def get_bucket_location(self, bucket_name) -> str:
        # Some buckets might have region set to None example, buckets created by cloudtrail service.
        # in such cases the bucket is globally available without Location Constraint, this method will return
        # GLOBAL in those cases in place of the region.
        s3_bucket_region = self.s3_client.get_bucket_location(
            Bucket=bucket_name
        ).get('LocationConstraint')
        self.logger.info(f"bucket name {bucket_name} and location {s3_bucket_region}")
        if s3_bucket_region is None:
            return "GLOBAL"
        return s3_bucket_region

    @resource_not_found_exception_handler
    def get_bucket_policy(self, bucket_name) -> GetBucketPolicyOutputTypeDef:
        self.logger.debug(f"Retrieving Policy for Bucket: {bucket_name}")
        response = self.s3_client.get_bucket_policy(
            Bucket=bucket_name
        )
        self.logger.debug(f"Bucket Policy: {response}")
        return response

    def read_json_file(self, bucket_name: str, file_qualified_name: str) -> Dict:
        response = self.s3_client.get_object(Bucket=bucket_name, Key=file_qualified_name)
        file_content = response['Body'].read().decode('utf-8')
        return json.loads(file_content)

    def copy_file(self, source_bucket_name: str, target_bucket_name: str, source_prefix: str, target_prefix: str,
                  file_name: str):
        source_key = source_prefix + file_name
        target_key = target_prefix + file_name
        self.logger.debug(f"Copy {source_key} from {source_bucket_name}")

        try:
            self.s3_client.copy_object(
                CopySource={
                    "Bucket": source_bucket_name,
                    "Key": source_key,
                },
                Bucket=target_bucket_name,
                Key=target_key,
            )
            self.logger.debug(f"Copied {target_key} to {target_bucket_name}")

        except ClientError as err:
            self.logger.error("Failed to copy key " + source_key)
            if err.response['Error']['Code'] == 'AccessDenied':
                self.logger.error(
                    'Access denied, make sure (1) the key exists in source bucket, (2) this lambda function '
                    'has s3:read permissions to the source bucket and (3) s3:put permissions to the target '
                    'bucket')
            self.logger.error(str(err))
            raise

    def write_json_as_file(self, bucket_name: str, qualified_file_name: str, json_object: Dict):
        try:
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=qualified_file_name,
                Body=(json.dumps(json_object)),
                ContentType="text/json",
                Metadata={
                    'Content-Type': "text/json"
                }
            )
        except ClientError as err:
            self.logger.error(str(err))
            raise


class Glacier:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('glacier', credentials=account_credentials, region=region)
        self.glacier_client = boto_session.get_client()

    @service_exception_handler
    def list_vaults(self) -> list[DescribeVaultOutputTypeDef]:
        response: ListVaultsOutputTypeDef = self.glacier_client.list_vaults()

        vault_list = response.get('VaultList', [])
        marker = response.get('Marker', None)

        while marker is not None:
            self.logger.debug(f"Marker Returned: {marker})")
            response = self.glacier_client.list_vaults(
                Marker=marker
            )
            self.logger.info("Extending Vault List")
            vault_list.extend(response.get('VaultList', []))
            marker = response.get('Marker', None)

        return vault_list

    @resource_not_found_exception_handler
    def get_vault_access_policy(self, vault_name) -> VaultAccessPolicyTypeDef:
        response = self.glacier_client.get_vault_access_policy(
            vaultName=vault_name
        )
        self.logger.debug(f"Vault Policy: {response}")
        return response['policy']
