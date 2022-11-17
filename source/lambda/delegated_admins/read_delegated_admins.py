# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

from delegated_admins.delegated_admins_repository import DelegatedAdminsRepository
from utils.api_gateway_lambda_handler import GenericApiGatewayEventHandler, ApiGatewayResponse, ResultListWrapper
from aws_lambda_powertools import Tracer

tracer = Tracer()


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> ApiGatewayResponse:
    return GenericApiGatewayEventHandler().handle_and_create_response(
        event,
        context,
        ReadDelegatedAdmins().read_delegated_admins
    )


class ReadDelegatedAdmins:

    def read_delegated_admins(self, _event: APIGatewayProxyEvent, _context: LambdaContext) -> ResultListWrapper:
        repository = DelegatedAdminsRepository()
        return {
            'Results': repository.find_all_delegated_admins()
        }
