#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv

from aws.utils.exceptions import service_exception_handler

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws_lambda_powertools import Logger
from mypy_boto3_glue.type_defs import GetResourcePoliciesResponseTypeDef, GluePolicyTypeDef


class Glue:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('glue', credentials=account_credentials, region=region)
        self.glue_client = boto_session.get_client()

    @service_exception_handler
    def get_resource_policies(self) -> list[GluePolicyTypeDef]:
        response: GetResourcePoliciesResponseTypeDef = self.glue_client.get_resource_policies()

        glue_resource_policies = response.get('GetResourcePoliciesResponseList', [])
        next_token = response.get('NextToken', None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.glue_client.get_resource_policies(
                NextToken=next_token
            )
            self.logger.info("Extending Glue Resource Policies")
            glue_resource_policies.extend(response.get('GetResourcePoliciesResponseList', []))
            next_token = response.get('NextToken', None)

        return glue_resource_policies

