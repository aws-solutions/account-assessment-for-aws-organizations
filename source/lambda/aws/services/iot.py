# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv

from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws_lambda_powertools import Logger
from mypy_boto3_iot.type_defs import PolicyTypeDef, GetPolicyResponseTypeDef, ListPoliciesResponseTypeDef


class IoT:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('iot', credentials=account_credentials, region=region)
        self.iot_client = boto_session.get_client()

    @service_exception_handler
    def list_policies(self) -> list[PolicyTypeDef]:
        response: ListPoliciesResponseTypeDef = self.iot_client.list_policies(
            ascendingOrder=True
        )

        iot_policies = response.get('policies', [])
        marker = response.get('nextMarker', None)

        while marker is not None:
            self.logger.debug(f"Marker Returned: {marker})")
            response = self.iot_client.list_policies(
                ascendingOrder=True,
                Marker=marker
            )
            self.logger.info("Extending IoT Policies")
            iot_policies.extend(response.get('policies', []))
            marker = response.get('nextMarker', None)

        return iot_policies

    @resource_not_found_exception_handler
    def get_policy(self, policy_name) -> GetPolicyResponseTypeDef:
        response = self.iot_client.get_policy(
            policyName=policy_name
        )
        self.logger.debug(f"IoT Policy: {response}")
        return response
