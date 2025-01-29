#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv


from aws_lambda_powertools import Logger
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler
from mypy_boto3_ssm_incidents.type_defs import ListResponsePlansOutputTypeDef, ResponsePlanSummaryTypeDef, \
    GetResourcePoliciesOutputTypeDef, ResourcePolicyTypeDef
from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session


class SSMIncidents:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('ssm-incidents', credentials=account_credentials, region=region)
        self.ssm_incidents_client = boto_session.get_client()

    @service_exception_handler
    def list_response_plans(self) -> list[ResponsePlanSummaryTypeDef]:
        response: ListResponsePlansOutputTypeDef = self.ssm_incidents_client.list_response_plans()

        response_plans = response.get('responsePlanSummaries', [])
        next_token = response.get('nextToken', None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.ssm_incidents_client.list_response_plans(
                nextToken=next_token
            )
            self.logger.info("Extending Response Plan List")
            response_plans.extend(response.get('responsePlanSummaries', []))
            next_token = response.get('nextToken', None)

        return response_plans

    @resource_not_found_exception_handler
    def get_resource_policies(self, resource_arn: str) -> list[ResourcePolicyTypeDef]:
        response: GetResourcePoliciesOutputTypeDef = self.ssm_incidents_client.get_resource_policies(
            resourceArn=resource_arn
        )
        self.logger.debug(f"Resource Policies: {response}")
        return response.get('resourcePolicies')


