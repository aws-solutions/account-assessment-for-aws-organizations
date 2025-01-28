#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import re
from os import getenv
from typing import Dict, List

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from assessment_runner.assessment_runner import AssessmentRunner, SynchronousScanStrategy
from assessment_runner.job_model import AssessmentType
from policy_explorer.policy_explorer_model import DynamoDBPolicyItem, ScanServiceRequestModel
from policy_explorer.policy_explorer_repository import PoliciesRepository
from policy_explorer.step_functions_lambda.scan_policy_all_services_router import resolve_scan_method
from policy_explorer.supported_configuration.supported_regions_and_services import SupportedServices, SupportedRegions
from utils.api_gateway_lambda_handler import GenericApiGatewayEventHandler, ApiGatewayResponse, ClientException

BAD_REQUEST = 'Bad Request'

logger = Logger(getenv('LOG_LEVEL'))
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: Dict, context: LambdaContext) -> ApiGatewayResponse:
    return GenericApiGatewayEventHandler().handle_and_create_response(
        event,
        context,
        AssessmentRunner(ScanSingleServiceStrategy()).run_assessment
    )


class ScanSingleServiceStrategy(SynchronousScanStrategy):

    def __init__(self):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))

    def assessment_type(self) -> str:
        return str(AssessmentType.POLICY_EXPLORER.value + "_SINGLE")

    def scan(self, job_id, request_body: Dict) -> List[DynamoDBPolicyItem]:
        scan_config: ScanServiceRequestModel = self.parse_request(job_id, request_body)

        scan_method = resolve_scan_method(scan_config)

        policies: list[DynamoDBPolicyItem] = scan_method()
        for policy in policies:
            policy['JobId'] = job_id
        logger.info(f"Scanned {len(policies)} policies for service {scan_config.get('ServiceName')}")
        return policies

    def write(self, policies):
        PoliciesRepository().create_all(policies)

    def parse_request(self, job_id: str, request: Dict) -> ScanServiceRequestModel:
        scan_model: ScanServiceRequestModel = {
            'AccountId': parse_account_id(request),
            'ServiceName': parse_service_name(request),
            'Regions': parse_regions(request),
            'JobId': job_id
        }

        self.logger.debug(scan_model)
        return scan_model


def parse_regions(request) -> List[str]:
    supported_regions = SupportedRegions().regions()
    requested_regions = request['Regions']
    valid_regions = set(supported_regions).intersection(requested_regions)
    if len(valid_regions) == 0:
        logger.error(
            f"No valid region. Supported regions: {', '.join(supported_regions)}. Requested regions: {', '.join(requested_regions)}."
        )
        raise ClientException(BAD_REQUEST, 'No valid region')
    return list(valid_regions)


def retain_valid_values_from_request(attribute_name: str, request: Dict, all_valid_values: List[str]) \
        -> (List[str], List[str]):
    requested_values = request[attribute_name]
    valid_requested_values = set(all_valid_values).intersection(requested_values)
    if len(valid_requested_values) > 0:
        return list(valid_requested_values), []
    else:
        return [], [f'No valid {attribute_name} selected']


def parse_service_name(request):
    if request["ServiceName"] in SupportedServices().service_names():
        result = request["ServiceName"]
    else:
        raise ClientException(BAD_REQUEST,'Invalid service name')
    return result


def parse_account_id(request: ScanServiceRequestModel) -> str:
    # Verify via regex that account_id is a valid AWS account ID
    pattern = re.compile(r'^\d{12}$')
    if not pattern.match(request['AccountId']):
        raise ClientException(BAD_REQUEST,"Invalid AWS Account ID found")

    return request['AccountId']
