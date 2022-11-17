# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from resource_based_policy.supported_configuration.scan_config_repository import ScanConfigRepository
from resource_based_policy.supported_configuration.supported_regions_and_services import SupportedServices, \
    SupportedRegions
from utils.api_gateway_lambda_handler import ApiGatewayResponse, GenericApiGatewayEventHandler

tracer = Tracer()


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> ApiGatewayResponse:
    return GenericApiGatewayEventHandler().handle_and_create_response(
        event,
        context,
        ui_selection_options
    )


def ui_selection_options(_event, _context):
    return {
        'SavedConfigurations': ScanConfigRepository().find_all_scan_configs(),
        'SupportedServices': SupportedServices().get_supported_services(_event, _context),
        'SupportedRegions': SupportedRegions().get_supported_region_objects(_event, _context)
    }
