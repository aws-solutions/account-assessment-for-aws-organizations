# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from os import getenv
from typing import Callable, List

from aws_lambda_powertools import Logger

import policy_explorer.policy_explorer_model as model
from assessment_runner.assessment_runner import write_task_failure
from aws.utils.exceptions import ServiceUnavailable, RegionNotEnabled, ConnectionTimeout, \
    AccountAssessmentClientException, AccessDenied
from policy_explorer.step_functions_lambda.convert_policy_into_dynamodb_items import ConvertPolicyIntoDynamoDBItems


def scan_regions(event: model.ScanServiceRequestModel,
                 scan_single_region: Callable[[str], List[model.DynamoDBPolicyItem]]) -> \
        list[model.DynamoDBPolicyItem]:
    logger = Logger(service='scan_regions', level=getenv('LOG_LEVEL'))
    resources_in_all_regions = []
    for region in event['Regions']:
        try:
            resources_for_region = scan_single_region(region)
            resources_in_all_regions.extend(resources_for_region)
        except (ServiceUnavailable, RegionNotEnabled, ConnectionTimeout,
                AccountAssessmentClientException, AccessDenied) as err:
            logger.debug(f"[{event['AccountId']}][{event['ServiceName']}] Handling Error: {err.message}. Writing "
                         f"failed task to JobHistory DynamoDB Table")
            write_task_failure(
                event['JobId'],
                'POLICY_EXPLORER',
                event['AccountId'],
                region,
                event['ServiceName'],
                json.dumps(err.message) if hasattr(err, 'message') else json.dumps(err)
            )
    return resources_in_all_regions

class DenormalizePolicyDetailsIntoDynamoDBItems:
    def __init__(self, event):
        self.event = event
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))

    def model(self, resource: model.PolicyDetails) -> List[model.DynamoDBPolicyItem]:
        convert_policy_details_into_dynamodb_items = ConvertPolicyIntoDynamoDBItems()
        ddb_policy_detail_items = convert_policy_details_into_dynamodb_items.create_items(resource)
        self.logger.debug(f"Policy Details in ddb format: {ddb_policy_detail_items}")
        return ddb_policy_detail_items
