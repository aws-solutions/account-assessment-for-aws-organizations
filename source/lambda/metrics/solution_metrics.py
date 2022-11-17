# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from json import dumps
from os import getenv
from typing import List, Union

import requests
from aws_lambda_powertools import Logger

from delegated_admins.delegated_admin_model import DelegatedAdminModel
from metrics.metrics_model import MetricsDataModel, MetricResponseModel
from resource_based_policy.resource_based_policy_model import ResourceBasedPolicyResponseModel
from trusted_access_enabled_services.trusted_access_model import TrustedAccessModel
from utils.decimal_encoder import DecimalEncoder
from utils.string_manipulation import trim_string_split_to_list_get_last_item


class SolutionMetrics(object):
    def __init__(self):
        self.logger = Logger(level=getenv('LOG_LEVEL'))

    def send_metrics(
            self,
            assessment_type: str,
            findings: List[Union[ResourceBasedPolicyResponseModel, DelegatedAdminModel, TrustedAccessModel]]
    ):
        try:
            send_metrics = getenv('SEND_ANONYMOUS_DATA', '')
            if send_metrics.lower() == 'yes':
                data = self._generate_metrics(assessment_type, findings)
                metrics = self._denormalize_to_metrics_model(data)
                return self.post_metrics(metrics)
        except:
            pass

    def _generate_metrics(self, assessment_type, findings):
        services = set()
        account_ids = set()
        regions = set()

        for finding in findings:
            services.add(finding.get('ServiceName') or finding.get('ServicePrincipal'))
            account_ids.add(finding.get('AccountId'))
            regions.add(finding.get('Region'))

        services.discard(None)
        account_ids.discard(None)
        regions.discard(None)

        data: MetricsDataModel = {
            "AssessmentType": assessment_type,
            "FindingsCount": str(len(findings)),
            "ServicesCount": str(len(services)),
            "AccountsCount": str(len(account_ids)),
            "RegionsCount": str(len(regions))
        }
        return data

    def post_metrics(self, metrics):
        json_data = dumps(metrics, cls=DecimalEncoder)
        headers = {'content-type': 'application/json'}
        url = getenv('METRICS_URL', 'https://metrics.awssolutionsbuilder.com/generic')
        r = requests.post(url, data=json_data, headers=headers)
        code = r.status_code
        return code

    def _denormalize_to_metrics_model(self, data: MetricsDataModel):
        solution_id = getenv('SOLUTION_ID', 'SO0217')
        stack_id = getenv('STACK_ID', 'undefined')
        uuid = trim_string_split_to_list_get_last_item(stack_id, "/")
        model: MetricResponseModel = {
            'Solution': solution_id,
            'TimeStamp': str(datetime.utcnow().isoformat()),
            'UUID': uuid,
            'Data': data
        }
        self.logger.debug(model)
        return model
