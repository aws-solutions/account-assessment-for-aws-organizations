#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from os import getenv

from aws_lambda_powertools.utilities.typing import LambdaContext

from trusted_access_enabled_services.trusted_services_repository import TrustedServicesRepository
from utils.api_gateway_lambda_handler import ApiGatewayResponse, GenericApiGatewayEventHandler
from utils.pagination_model import PaginatedResponse
from utils.pagination_helper import extract_pagination_params, build_ddb_pagination
from aws_lambda_powertools import Tracer, Logger

logger = Logger(getenv('LOG_LEVEL'))
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=False)
def lambda_handler(event: dict, context: LambdaContext) -> ApiGatewayResponse:
    return GenericApiGatewayEventHandler().handle_and_create_response(
        event,
        context,
        ReadTrustedServices().read_trusted_access_enabled_services
    )


class ReadTrustedServices:

    def read_trusted_access_enabled_services(self, _event, _context) -> PaginatedResponse:
        repository = TrustedServicesRepository()

        if hasattr(_event, 'query_string_parameters'):
            query = _event.query_string_parameters or {}
        else:
            query = _event.get('queryStringParameters') or {}

        if query.get('maxResults') or query.get('nextToken') or query.get('limit'):
            pagination_params = extract_pagination_params(query)
            ddb_pagination = build_ddb_pagination(pagination_params)
            
            results, pagination_metadata = repository.find_all_trusted_services_paginated(ddb_pagination)
            
            return {
                'Results': results,
                'Pagination': pagination_metadata
            }
        else:
            return {
                'Results': repository.find_all_trusted_services(),
                'Pagination': {
                    'nextToken': None,
                    'hasMoreResults': False
                }
            }
