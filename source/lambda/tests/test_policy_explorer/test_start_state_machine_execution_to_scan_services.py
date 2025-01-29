#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os
import uuid

from aws_lambda_powertools import Logger
from moto import mock_aws

from aws.services.organizations import Organizations
from aws.services.step_functions import StepFunctions
from policy_explorer.start_state_machine_execution_to_scan_services import \
    ScanAllPoliciesStrategy
from policy_explorer.supported_configuration.supported_regions_and_services import SupportedRegions, \
    SupportedServices

logger = Logger(level="info")


@mock_aws
def test_start_scan(mocker, freeze_clock, organizations_setup, policy_explorer_table):
    # ARRANGE
    active_account_ids: list[str] = ['123456789012', '111122223333', '444455556666', '777788889999', '000000000000']
    mocker.patch.object(SupportedRegions, 'regions', return_value=['eu-central-1', 'us-east-1'])
    mocker.patch.object(SupportedServices, 'service_names', return_value=['config', 'cloudformation', 's3'])
    mocker.patch.object(Organizations, 'list_active_account_ids', return_value=active_account_ids)

    os.environ['SCAN_POLICIES_STATE_MACHINE_ARN'] = 'some-arn'
    start = mocker.patch.object(StepFunctions, 'start_execution', return_value=None)

    job_id = str(uuid.uuid4())

    # ACT
    ScanAllPoliciesStrategy().scan(job_id, {})

    # ASSERT
    start.assert_called_once_with('some-arn', {
        'JobId': job_id,
        'Scan': {
            "AccountIds": active_account_ids,
            "ServiceNames": ['config', 'cloudformation', 's3']
        }
    })

