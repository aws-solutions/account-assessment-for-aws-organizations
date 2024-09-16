# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv

from aws.utils.exceptions import service_exception_handler

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws_lambda_powertools import Logger
from mypy_boto3_apigateway.type_defs import RestApiResponseTypeDef

class APIGateway:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('apigateway', credentials=account_credentials, region=region)
        self.apigateway_client = boto_session.get_client()

    @service_exception_handler
    def get_rest_apis(self) -> list[RestApiResponseTypeDef]:
        response = self.apigateway_client.get_rest_apis()

        api_list = response.get('items', [])
        position = response.get('position', None)

        while position is not None:
            self.logger.debug(f"Current pagination position returned: {position})")
            response = self.apigateway_client.get_rest_apis(
                position=position
            )
            self.logger.info("Extending API List")
            api_list.extend(response.get('items', []))
            position = response.get('position', None)
        self.logger.debug(f"API List: {api_list}")
        return api_list

