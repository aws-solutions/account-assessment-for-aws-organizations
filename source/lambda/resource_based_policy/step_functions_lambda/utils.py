# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from datetime import datetime
from os import getenv
from typing import Iterable, Callable

from aws_lambda_powertools import Logger

import resource_based_policy.resource_based_policy_model as model
from assessment_runner.assessment_runner import write_task_failure
from aws.utils.exceptions import ServiceUnavailable, RegionNotEnabled, ConnectionTimeout, \
    AccountAssessmentClientException, AccessDenied


def scan_regions(event: model.ScanServiceRequestModel,
                 scan_single_region: Callable[[str], Iterable[model.ResourceBasedPolicyResponseModel]]) -> \
        list[model.ResourceBasedPolicyResponseModel]:
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
                'RESOURCE_BASED_POLICY',
                event['AccountId'],
                region,
                event['ServiceName'],
                json.dumps(err.message) if hasattr(err, 'message') else json.dumps(err)
            )
    return resources_in_all_regions


class DenormalizePolicyAnalyzerRequest:
    def __init__(self):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))

    def model(self, resource_name: str, policy: str) -> model.PolicyAnalyzerRequest:
        request: model.PolicyAnalyzerRequest = {
            "ResourceName": resource_name,
            "Policy": policy
        }
        self.logger.debug(f"PolicyAnalyzerRequestModel: {model}")
        return request


class DenormalizeResourceBasedPolicyResponse:
    def __init__(self, event):
        self.event = event
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))

    def model(self, resource: model.PolicyAnalyzerResponse, region='global'):
        event: model.ScanServiceRequestModel = self.event
        response: model.ResourceBasedPolicyResponseModel = {
            'ServiceName': event['ServiceName'],
            'AccountId': event['AccountId'],
            'ResourceName': resource['ResourceName'],
            'DependencyType': resource['GlobalContextKey'],
            'DependencyOn': resource['OrganizationsResource'],
            'JobId': event['JobId'],
            'AssessedAt': datetime.now().isoformat(),
            'Region': region
        }
        self.logger.debug(f"ResourceBasedPolicyResponseModel: {model}")
        return response
