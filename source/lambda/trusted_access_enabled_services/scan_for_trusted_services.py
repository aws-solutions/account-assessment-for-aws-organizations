#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
import traceback
from datetime import datetime, timezone
from os import getenv
from typing import List

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_organizations.type_defs import EnabledServicePrincipalTypeDef

from assessment_runner.assessment_runner import AssessmentRunner, SynchronousScanStrategy
from assessment_runner.job_model import AssessmentType
from aws.services.organizations import Organizations
from metrics.solution_metrics import SolutionMetrics
from trusted_access_enabled_services.trusted_access_model import TrustedAccessCreateRequest
from trusted_access_enabled_services.trusted_services_repository import TrustedServicesRepository
from utils.api_gateway_lambda_handler import ApiGatewayResponse, GenericApiGatewayEventHandler, default_headers
from utils.decimal_json_encoder import DecimalJsonEncoder

logger = Logger(getenv('LOG_LEVEL'))
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext) -> ApiGatewayResponse:
    try:
        return GenericApiGatewayEventHandler().handle_and_create_response(
            event,
            context,
            AssessmentRunner(TrustedAccessStrategy()).run_assessment
        )
    except Exception as error:
        logger.error(f"Error: {error}")
        logger.error(traceback.format_exc())
        error_type = type(error).__name__
        body = {
            "Error": error_type,
            "Message": "An unexpected error occurred. Inspect CloudWatch logs for more information.",
            "Timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
        return {
            'statusCode': 400,
            'body': json.dumps(body, cls=DecimalJsonEncoder),
            'headers': default_headers,
        }


class TrustedAccessStrategy(SynchronousScanStrategy):
    """
    Get the list of all services for which trusted access is enabled in the current aws organization.
    """

    def __init__(self):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.job_id = None

    def assessment_type(self) -> str: return str(AssessmentType.TRUSTED_ACCESS.value)

    def scan(self, job_id, request_body) -> List[TrustedAccessCreateRequest]:
        self.job_id = job_id
        enabled_service_principals = Organizations().list_aws_service_access_for_organization()
        self.logger.debug(f"Trusted Access Enabled Services: {enabled_service_principals}")

        return list(self._map_to_trusted_access_model(service) for service in enabled_service_principals)

    def _map_to_trusted_access_model(self, service: EnabledServicePrincipalTypeDef) -> TrustedAccessCreateRequest:
        model: TrustedAccessCreateRequest = {
            'DateEnabled': service['DateEnabled'].isoformat(),
            'ServicePrincipal': service['ServicePrincipal'],
            'JobId': self.job_id,
            'AssessedAt': datetime.now().isoformat(),
        }
        self.logger.debug(model)
        return model

    def write(self, trusted_services: List[TrustedAccessCreateRequest]):
        findings = TrustedServicesRepository().create_all(trusted_services)
        SolutionMetrics().send_scan_metrics(self.assessment_type(), findings)
