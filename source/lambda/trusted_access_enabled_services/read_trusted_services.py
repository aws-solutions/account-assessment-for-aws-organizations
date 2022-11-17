# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools.utilities.typing import LambdaContext

from trusted_access_enabled_services.trusted_services_repository import TrustedServicesRepository
from utils.api_gateway_lambda_handler import ApiGatewayResponse, GenericApiGatewayEventHandler, ResultListWrapper
from aws_lambda_powertools import Tracer

tracer = Tracer()


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> ApiGatewayResponse:
    return GenericApiGatewayEventHandler().handle_and_create_response(
        event,
        context,
        ReadTrustedServices().read_trusted_access_enabled_services
    )


class ReadTrustedServices:

    def read_trusted_access_enabled_services(self, _event, _context) -> ResultListWrapper:
        repository = TrustedServicesRepository()
        return {
            'Results': repository.find_all_trusted_services()
        }
