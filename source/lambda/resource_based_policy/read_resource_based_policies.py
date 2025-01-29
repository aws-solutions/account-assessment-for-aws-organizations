#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from os import getenv

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

from assessment_runner.job_model import JobStatus
from assessment_runner.jobs_repository import JobsRepository
from resource_based_policy.resource_based_policies_repository import ResourceBasedPoliciesRepository
from utils.api_gateway_lambda_handler import ApiGatewayResponse, GenericApiGatewayEventHandler, \
    AsynchronousResultListWrapper
from aws_lambda_powertools import Tracer, Logger

logger = Logger(getenv('LOG_LEVEL'))
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext) -> ApiGatewayResponse:
    return GenericApiGatewayEventHandler().handle_and_create_response(
        event,
        context,
        ReadResourceBasedPolicies().read_resource_based_policies
    )


class ReadResourceBasedPolicies:

    def read_resource_based_policies(self,
                                     _event: APIGatewayProxyEvent,
                                     _context: LambdaContext) -> AsynchronousResultListWrapper:
        all_resource_based_policies = ResourceBasedPoliciesRepository().find_all_policies()
        last_job = JobsRepository().get_last_job_marker('RESOURCE_BASED_POLICY')

        response = {
            'ScanInProgress': last_job == str(JobStatus.ACTIVE.value),
            'Results': all_resource_based_policies
        }

        return response
