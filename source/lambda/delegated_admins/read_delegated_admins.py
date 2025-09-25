#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from os import getenv

from aws_lambda_powertools.utilities.typing import LambdaContext

from delegated_admins.delegated_admins_repository import DelegatedAdminsRepository
from utils.api_gateway_lambda_handler import GenericApiGatewayEventHandler, ApiGatewayResponse
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
        ReadDelegatedAdmins().read_delegated_admins
    )


class ReadDelegatedAdmins:

    def read_delegated_admins(self, _event, _context) -> PaginatedResponse:
        repository = DelegatedAdminsRepository()

        if hasattr(_event, 'query_string_parameters'):
            query = _event.query_string_parameters or {}
        else:
            query = _event.get('queryStringParameters') or {}

        if query.get('maxResults') or query.get('nextToken') or query.get('limit'):
            pagination_params = extract_pagination_params(query)
            ddb_pagination = build_ddb_pagination(pagination_params)
            
            results, pagination_metadata = repository.find_all_delegated_admins_paginated(ddb_pagination)
            
            return {
                'Results': results,
                'Pagination': pagination_metadata
            }
        else:
            return {
                'Results': repository.find_all_delegated_admins(),
                'Pagination': {
                    'nextToken': None,
                    'hasMoreResults': False
                }
            }
