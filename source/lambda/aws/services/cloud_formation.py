# Copyright Amazon.com,Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# !/bin/python

from os import getenv
from typing import TYPE_CHECKING
from typing import Iterable
from aws_lambda_powertools import Logger
from mypy_boto3_cloudformation.type_defs import (
    ListStacksOutputTypeDef,
    GetStackPolicyOutputTypeDef,
    StackSetSummaryTypeDef,
    StackSetTypeDef,
    StackSummaryTypeDef,
)
from aws.utils.exceptions import (
    service_exception_handler,
    resource_not_found_exception_handler,
)

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session


class CloudFormation:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv("LOG_LEVEL"))
        self.region = region
        role_name = getenv("SPOKE_ROLE_NAME")
        self.logger.debug(
            f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}"
        )
        account_credentials = SecurityTokenService().assume_role_by_name(
            account_id, role_name
        )
        boto_session = Boto3Session(
            "cloudformation", credentials=account_credentials, region=region
        )
        self.cloudformation_client = boto_session.get_client()

    @service_exception_handler
    def list_stacks(self) -> list[StackSummaryTypeDef]:
        response: ListStacksOutputTypeDef = self.cloudformation_client.list_stacks()

        stack_summaries = response.get("StackSummaries", [])
        next_token = response.get("NextToken", None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.cloudformation_client.list_stacks(NextToken=next_token)
            self.logger.info("Extending Stack Summaries")
            stack_summaries.extend(response.get("StackSummaries", []))
            next_token = response.get("NextToken", None)
        self.logger.debug(stack_summaries)

        filtered_undeleted_stacks = list(
            filter(lambda stack: "DELETE" not in stack["StackStatus"], stack_summaries)
        )
        self.logger.debug(filtered_undeleted_stacks)

        return filtered_undeleted_stacks

    @resource_not_found_exception_handler
    def get_stack_policy(self, stack_name: str) -> GetStackPolicyOutputTypeDef:
        response: GetStackPolicyOutputTypeDef = (
            self.cloudformation_client.get_stack_policy(StackName=stack_name)
        )
        self.logger.debug(f"CloudFormation Stack Policy: {response}")
        return response

    @service_exception_handler
    def list_stack_sets(self) -> list[StackSetSummaryTypeDef]:
        response: StackSummaryTypeDef = self.cloudformation_client.list_stack_sets(
            Status="ACTIVE", CallAs="DELEGATED_ADMIN"
        )

        stack_set_summaries = response.get("Summaries", [])
        next_token = response.get("NextToken", None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.cloudformation_client.list_stack_sets(
                Status="ACTIVE", CallAs="DELEGATED_ADMIN", NextToken=next_token
            )
            self.logger.info("Extending Stack Set Summaries")
            stack_set_summaries.extend(response.get("Summaries", []))
            next_token = response.get("NextToken", None)
        return stack_set_summaries

    @resource_not_found_exception_handler
    def describe_stack_set(self, stack_set_name: str) -> StackSetTypeDef:
        response = self.cloudformation_client.describe_stack_set(
            StackSetName=stack_set_name
        )
        stack_set_details = response.get("StackSet")
        if stack_set_details and "OrganizationalUnitIds" in stack_set_details:
            ou_ids = stack_set_details["OrganizationalUnitIds"]
        else:
            ou_ids = []

        return ou_ids
