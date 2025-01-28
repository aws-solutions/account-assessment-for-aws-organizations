# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_redshift_serverless.type_defs import SnapshotTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.redshift_serverless import RedshiftServerless
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn

class RedshiftServerlessPolicy:
    
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']
    
    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)
    
    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning Redshift Serverless resource policies in {region}")
        redshift_serverless_client = RedshiftServerless(self.account_id, region)
        snapshots: list[SnapshotTypeDef] = redshift_serverless_client.list_snapshots()
        snapshots_and_policies: list[model.PolicyDetails] = self._get_snapshots_and_policies(snapshots, redshift_serverless_client)
        snapshot_policies_dynamodb_items = []
        for snapshot_policy in snapshots_and_policies:
            if snapshot_policy.get('Policy'):
                snapshot_policies_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(snapshot_policy))
        return snapshot_policies_dynamodb_items
        
    def _get_snapshots_and_policies(self, snapshots: list[SnapshotTypeDef], redshift_serverless_client: RedshiftServerless) -> list[model.PolicyDetails]:
        return list(self._get_snapshot_resource_policy(snapshot, redshift_serverless_client) for snapshot in snapshots)
    
    @staticmethod
    def _get_snapshot_resource_policy(snapshot: SnapshotTypeDef, redshift_serverless_client: RedshiftServerless) -> model.PolicyDetails:
        resource_arn = snapshot.get('snapshotArn')
        policy_details = get_policy_details_from_arn(resource_arn)
        policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
        resource_policy: str = redshift_serverless_client.get_resource_policy(snapshot.get('snapshotArn'))
        policy_details.update({'Policy': resource_policy})
        return policy_details