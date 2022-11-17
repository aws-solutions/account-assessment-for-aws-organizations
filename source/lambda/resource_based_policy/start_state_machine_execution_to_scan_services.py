# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import re
from os import getenv
from typing import List, Dict

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from assessment_runner.assessment_runner import AssessmentRunner, ScanStrategy
from assessment_runner.job_model import AssessmentType
from aws.services.organizations import Organizations
from aws.services.step_functions import StepFunctions
from resource_based_policy.resource_based_policy_model import ScanModel
from resource_based_policy.supported_configuration.scan_config_repository import ScanConfigRepository
from resource_based_policy.supported_configuration.scan_configuration_model import ScanConfigModel
from resource_based_policy.supported_configuration.supported_regions_and_services import SupportedServices, \
    SupportedRegions
from utils.api_gateway_lambda_handler import ApiGatewayResponse, GenericApiGatewayEventHandler, ClientException

AWS_ORG_UNIT_ID_REGEX = re.compile("ou-[a-z0-9]{4,32}-[a-z0-9]{8,32}")
tracer = Tracer()


@tracer.capture_lambda_handler
def lambda_handler(event: Dict, context: LambdaContext) -> ApiGatewayResponse:
    return GenericApiGatewayEventHandler().handle_and_create_response(
        event,
        context,
        AssessmentRunner(ResourceBasedPolicyStrategy()).run_assessment
    )


class ResourceBasedPolicyStrategy(ScanStrategy):
    """
    search the active accounts in aws organizations and start state machine execution to assess resource based
    policies in the accounts.
    """

    def __init__(self):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.state_machine_arn = getenv('SCAN_RESOURCE_POLICY_STATE_MACHINE_ARN')

    def assessment_type(self) -> str:
        return str(AssessmentType.RESOURCE_BASED_POLICY.value)

    def scan(self, job_id, request_body: Dict):
        scan_config: ScanModel = self.parse_request(request_body)

        if request_body.get('ConfigurationName'):
            ScanConfigRepository().create_scan_config(request_body)

        state_machine_input = {
            'JobId': job_id,
            'Scan': scan_config
        }
        StepFunctions().start_execution(self.state_machine_arn, state_machine_input)

    def parse_request(self, request: ScanConfigModel) -> ScanModel:
        scan_model = {}

        account_ids, errors = self.parse_account_ids(request)
        scan_model['AccountIds'] = account_ids

        valid_org_ids, new_errors = parse_attribute_from_request(
            'ServiceNames',
            request,
            SupportedServices().service_names())
        scan_model['ServiceNames'] = valid_org_ids
        errors = errors + new_errors

        valid_org_ids, new_errors = parse_attribute_from_request(
            'Regions',
            request,
            SupportedRegions().regions())
        scan_model['Regions'] = valid_org_ids
        errors = errors + new_errors

        if request.get('ConfigurationName'):
            config_name_pattern = re.compile("^[a-zA-Z0-9_-]{1,64}$")
            if not config_name_pattern.fullmatch(request['ConfigurationName']):
                errors = errors + ['Invalid configuration name.']

        if len(errors) > 0:
            raise ClientException("Validation Error", ', '.join(str(err) for err in errors))

        self.logger.debug(scan_model)
        return scan_model

    def parse_account_ids(self, request: ScanConfigModel) -> (List[str], List[str]):
        if 'OrgUnitIds' in request.keys():
            return self.resolve_account_id_from_org_units(request)
        else:
            return parse_attribute_from_request(
                'AccountIds',
                request,
                Organizations().list_active_account_ids())

    def resolve_account_id_from_org_units(self, request) -> (List[str], List[str]):
        requested_org_units = set(request['OrgUnitIds'])

        valid_org_ids = list(org_unit for org_unit in requested_org_units if re.match(AWS_ORG_UNIT_ID_REGEX, org_unit))
        invalid_org_ids = requested_org_units.difference(valid_org_ids)

        if len(invalid_org_ids):
            return list(), ['Invalid OrgUnitIds: ' + ', '.join(invalid_org_ids)]

        return Organizations().get_account_ids_in_org_units(valid_org_ids), []


def parse_attribute_from_request(attribute_name: str, request: Dict, all_valid_values: List[str]) \
        -> (List[str], List[str]):
    if attribute_name in request.keys():
        return retain_valid_values_from_request(attribute_name, request, all_valid_values)
    else:
        return all_valid_values, []


def retain_valid_values_from_request(attribute_name: str, request: Dict, all_valid_values: List[str]) \
        -> (List[str], List[str]):
    requested_values = request[attribute_name]
    valid_requested_values = set(all_valid_values).intersection(requested_values)
    if len(valid_requested_values) > 0:
        return list(valid_requested_values), []
    else:
        return [], [f'No valid {attribute_name} selected']
