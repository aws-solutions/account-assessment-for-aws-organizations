#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv

from aws.utils.exceptions import service_exception_handler

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws_lambda_powertools import Logger
from mypy_boto3_events.type_defs import EventBusTypeDef, ListEventBusesResponseTypeDef


class Events:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('events', credentials=account_credentials, region=region)
        self.events_client = boto_session.get_client()

    @service_exception_handler
    def list_event_buses(self) -> list[EventBusTypeDef]:
        response: ListEventBusesResponseTypeDef = self.events_client.list_event_buses()

        event_buses = response.get('EventBuses', [])
        next_token = response.get('NextToken', None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.events_client.list_event_buses(
                NextToken=next_token
            )
            self.logger.info("Extending Event Bus List")
            event_buses.extend(response.get('EventBuses', []))
            next_token = response.get('NextToken', None)

        return event_buses

