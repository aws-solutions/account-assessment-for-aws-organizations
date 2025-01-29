#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv

from aws_lambda_powertools import Logger
from mypy_boto3_ec2.type_defs import DescribeVpcEndpointsResultTypeDef, VpcEndpointTypeDef
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session


class EC2:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('ec2', credentials=account_credentials, region=region)
        self.ec2_client = boto_session.get_client()

    @service_exception_handler
    def describe_vpc_endpoints(self) -> list[VpcEndpointTypeDef]:
        response: DescribeVpcEndpointsResultTypeDef = self.ec2_client.describe_vpc_endpoints()

        repositories = response.get('VpcEndpoints', [])
        next_token = response.get('NextToken', None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.ec2_client.describe_vpc_endpoints(
                NextToken=next_token
            )
            self.logger.info("Extending VPC Endpoint List")
            repositories.extend(response.get('VpcEndpoints', []))
            next_token = response.get('NextToken', None)

        return repositories



