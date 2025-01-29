#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler
from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws_lambda_powertools import Logger
from mypy_boto3_lambda.type_defs import FunctionConfigurationTypeDef, GetPolicyResponseTypeDef, ListFunctionsResponseTypeDef


class LambdaFunctions:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('lambda', credentials=account_credentials, region=region)
        self.lambda_client = boto_session.get_client()

    @service_exception_handler
    def list_functions(self) -> list[FunctionConfigurationTypeDef]:
        response: ListFunctionsResponseTypeDef = self.lambda_client.list_functions(
            FunctionVersion='ALL',
        )

        function_list = response.get('Functions', [])
        marker = response.get('NextMarker', None)

        while marker is not None:
            self.logger.debug(f"Marker Returned: {marker})")
            response = self.lambda_client.list_functions(
                FunctionVersion='ALL',
                Marker=marker
            )
            self.logger.info("Extending Function List")
            function_list.extend(response.get('Functions', []))
            marker = response.get('NextMarker', None)

        return function_list

    @resource_not_found_exception_handler
    def get_policy(self, function_arn) -> GetPolicyResponseTypeDef:
        response = self.lambda_client.get_policy(
            FunctionName=function_arn
        )
        self.logger.debug(f"Lambda Policy: {response}")
        return response

