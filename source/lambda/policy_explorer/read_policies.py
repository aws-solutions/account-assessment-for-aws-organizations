#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from os import getenv

from aws_lambda_powertools import Tracer, Logger
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

from metrics.solution_metrics import SolutionMetrics
from policy_explorer.policy_explorer_model import PolicyFilters, DdbPagination, PolicySearchResponse
from policy_explorer.policy_explorer_repository import PoliciesRepository
from utils.api_gateway_lambda_handler import GenericApiGatewayEventHandler, ApiGatewayResponse, ClientException
from utils.pagination_helper import validate_max_results, decode_next_token

tracer = Tracer()
logger = Logger(getenv('LOG_LEVEL'))


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext) -> ApiGatewayResponse:
    return GenericApiGatewayEventHandler().handle_and_create_response(
        event,
        context,
        ReadPolicies().read_policies
    )


class ReadPolicies:

    def read_policies(self, _event: APIGatewayProxyEvent, _context: LambdaContext) -> PolicySearchResponse:
        repository = PoliciesRepository()

        policy_type = _event.path_parameters.get('partitionKey')
        if policy_type not in ['ServiceControlPolicy', 'ResourceBasedPolicy', 'IdentityBasedPolicy']:
            raise ClientException('Invalid policy type')

        query = _event.query_string_parameters
        region = query.get('region')
        if not region:
            raise ClientException('Query parameter "region" is required')

        filters: PolicyFilters = dict()
        if query.get('principal'):
            filters['Principal'] = query.get('principal')
        if query.get('notPrincipal'):
            filters['NotPrincipal'] = query.get('notPrincipal')
        if query.get('action'):
            filters['Action'] = query.get('action')
        if query.get('notAction'):
            filters['NotAction'] = query.get('notAction')
        if query.get('resource'):
            filters['Resource'] = query.get('resource')
        if query.get('notResource'):
            filters['NotResource'] = query.get('notResource')
        if query.get('effect'):
            filters['Effect'] = query.get('effect')
        if query.get('condition'):
            filters['Condition'] = query.get('condition')

        max_results_param = query.get('maxResults') or query.get('limit')
        max_results = validate_max_results(max_results_param)
        exclusive_start_key = decode_next_token(query.get('nextToken'))

        pagination: DdbPagination = dict(
            Limit=max_results,
            ExclusiveStartKey=exclusive_start_key
        )

        results, pagination_metadata = repository.find_all_by_policy_type(policy_type, region, filters, pagination)

        SolutionMetrics().send_search_metrics(policy_type, region, filters, len(results))

        response: PolicySearchResponse = {
            'Results': results,
            'Pagination': pagination_metadata
        }

        return response