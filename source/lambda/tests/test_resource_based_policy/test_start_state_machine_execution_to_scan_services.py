# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
import os
import uuid

import pytest
from aws_lambda_powertools import Logger
from moto import mock_sts

from aws.services.step_functions import StepFunctions
from resource_based_policy.start_state_machine_execution_to_scan_services import \
    ResourceBasedPolicyStrategy
from resource_based_policy.supported_configuration.scan_config_repository import PARTITION_KEY_SCAN_CONFIGS
from resource_based_policy.supported_configuration.scan_configuration_model import ScanConfigModel
from resource_based_policy.supported_configuration.supported_regions_and_services import SupportedRegions, \
    SupportedServices
from utils.api_gateway_lambda_handler import ClientException
from utils.base_repository import BaseRepository

logger = Logger(level="info")


def describe_parse_request():
    @mock_sts
    def test_collects_validation_errors(mocker, organizations_setup):
        # ARRANGE
        mocker.patch.object(SupportedRegions, 'regions', return_value=['eu-central-1'])
        mocker.patch.object(SupportedServices, 'service_names', return_value=['config', 'cloudformation'])

        # neither AccountIds, Regions nor Service Names are supported/valid in this case
        request_body: ScanConfigModel = {
            "AccountIds": ['111111111111', '222222222222'],
            "Regions": ['us-east-1'],
            "ServiceNames": ['s3']
        }

        # ACT
        with pytest.raises(ClientException) as exception_data:
            ResourceBasedPolicyStrategy().parse_request(request_body)

        # ASSERT
        e = exception_data.value
        assert e.error == "Validation Error"
        assert e.message == 'No valid AccountIds selected, No valid ServiceNames selected, No valid Regions selected'

    @mock_sts
    def test_raises_error_for_invalid_org_unit(mocker, organizations_setup):
        # ARRANGE
        mocker.patch.object(SupportedRegions, 'regions', return_value={'eu-central-1'})
        mocker.patch.object(SupportedServices, 'service_names', return_value={'config', 'cloudformation'})

        # neither AccountIds, Regions nor Service Names are supported/valid in this case
        request_body: ScanConfigModel = {
            "OrgUnitIds": ['this-is-invalid'],
            "Regions": ['eu-central-1'],
            "ServiceNames": ['config']
        }

        # ACT
        with pytest.raises(ClientException) as exception_data:
            ResourceBasedPolicyStrategy().parse_request(request_body)

        # ASSERT
        e = exception_data.value
        assert e.error == "Validation Error"
        assert e.message == 'Invalid OrgUnitIds: this-is-invalid'

    @mock_sts
    def test_raises_error_for_invalid_configuration_name(mocker, organizations_setup):
        # ARRANGE
        account_id = organizations_setup['dev_account_id']
        mocker.patch.object(SupportedRegions, 'regions', return_value={'eu-central-1'})
        mocker.patch.object(SupportedServices, 'service_names', return_value={'config', 'cloudformation'})

        # neither AccountIds, Regions nor Service Names are supported/valid in this case
        request_body: ScanConfigModel = {
            "AccountIds": [account_id],
            "Regions": ['eu-central-1'],
            "ServiceNames": ['config'],
            "ConfigurationName": 'has !invalid characters',
        }

        # ACT
        with pytest.raises(ClientException) as exception_data:
            ResourceBasedPolicyStrategy().parse_request(request_body)

        # ASSERT
        e = exception_data.value
        assert e.error == "Validation Error"
        assert e.message == 'Invalid configuration name.'

    @mock_sts
    def test_parses_all_attributes(mocker, organizations_setup):
        # ARRANGE
        account_id = organizations_setup['dev_account_id']
        mocker.patch.object(SupportedRegions, 'regions', return_value=['eu-central-1', 'us-east-1'])
        mocker.patch.object(SupportedServices, 'service_names', return_value=['config', 'cloudformation', 's3'])

        request_body: ScanConfigModel = {
            "AccountIds": [account_id],
            "Regions": ['us-east-1'],
            "ServiceNames": ['config', 's3']
        }

        # ACT
        parsed_request = ResourceBasedPolicyStrategy().parse_request(request_body)

        # ASSERT
        assert parsed_request['AccountIds'] == request_body['AccountIds']
        assert parsed_request['Regions'] == request_body['Regions']
        assert set(parsed_request['ServiceNames']) == set(request_body['ServiceNames'])

    @mock_sts
    def test_replaces_empty_attribute_by_all_valid_values(mocker, organizations_setup):
        # ARRANGE
        existing_account_id = organizations_setup['dev_account_id']
        mocker.patch.object(SupportedRegions, 'regions', return_value=['eu-central-1', 'us-east-1'])
        mocker.patch.object(SupportedServices, 'service_names', return_value=['config', 'cloudformation', 's3'])

        request_body: ScanConfigModel = {
            "AccountIds": [existing_account_id],
            "Regions": ['us-east-1'],
        }

        # ACT
        parsed_request = ResourceBasedPolicyStrategy().parse_request(request_body)

        # ASSERT
        assert parsed_request['ServiceNames'] == ['config', 'cloudformation', 's3']

    @mock_sts
    def test_resolves_org_unit_to_account_ids(mocker, organizations_setup):
        # ARRANGE
        org_unit_id = organizations_setup['dev_ou_id']
        mocker.patch.object(SupportedRegions, 'regions', return_value=['eu-central-1', 'us-east-1'])
        mocker.patch.object(SupportedServices, 'service_names', return_value=['config', 'cloudformation', 's3'])

        request_body: ScanConfigModel = {
            "OrgUnitIds": [org_unit_id],
            "Regions": ['us-east-1'],
            "ServiceNames": ['s3']
        }

        # ACT
        parsed_request = ResourceBasedPolicyStrategy().parse_request(request_body)

        # ASSERT
        account_ids_in_org_unit = [organizations_setup['dev_account_id'], organizations_setup['dev_account_id_2']]
        assert parsed_request['AccountIds'] == account_ids_in_org_unit

    @mock_sts
    def test_parses_full_scan(mocker, organizations_setup):
        # ARRANGE
        existing_account_id = organizations_setup['dev_account_id']
        mocker.patch.object(SupportedRegions, 'regions', return_value=['eu-central-1', 'us-east-1'])
        mocker.patch.object(SupportedServices, 'service_names', return_value=['config', 'cloudformation', 's3'])

        full_scan_request_body: ScanConfigModel = {}

        # ACT
        parsed_request = ResourceBasedPolicyStrategy().parse_request(full_scan_request_body)

        # ASSERT
        assert parsed_request['ServiceNames'] == ['config', 'cloudformation', 's3']
        assert parsed_request['Regions'] == ['eu-central-1', 'us-east-1']
        assert set(parsed_request['AccountIds']).issuperset({existing_account_id})
        assert json.dumps(parsed_request)  # verify the request is JSON serializable


@mock_sts
def test_start_scan(mocker, freeze_clock, organizations_setup, resource_based_policies_table):
    # ARRANGE
    existing_account_id = organizations_setup['dev_account_id']
    mocker.patch.object(SupportedRegions, 'regions', return_value=['eu-central-1', 'us-east-1'])
    mocker.patch.object(SupportedServices, 'service_names', return_value=['config', 'cloudformation', 's3'])

    os.environ['SCAN_RESOURCE_POLICY_STATE_MACHINE_ARN'] = 'some-arn'
    start = mocker.patch.object(StepFunctions, 'start_execution', return_value=None)

    job_id = str(uuid.uuid4())
    request_body = {
        "AccountIds": [existing_account_id],
        "Regions": ['us-east-1'],
        "ServiceNames": ['s3'],
        "ConfigurationName": 'us-east-1_s3_scan'
    }

    # ACT
    ResourceBasedPolicyStrategy().scan(job_id, request_body)

    # ASSERT
    start.assert_called_once_with('some-arn', {
        'JobId': job_id,
        'Scan': {
            "AccountIds": [existing_account_id],
            "Regions": ['us-east-1'],
            "ServiceNames": ['s3']
        }
    })
    response = resource_based_policies_table.get_item(
        Key={'PartitionKey': PARTITION_KEY_SCAN_CONFIGS,
             'SortKey': 'us-east-1_s3_scan'}
    )
    assert response['Item'] == {
        **request_body,
        'PartitionKey': PARTITION_KEY_SCAN_CONFIGS,
        'SortKey': 'us-east-1_s3_scan',
        'ExpiresAt': BaseRepository()._calculate_expires_at()}
