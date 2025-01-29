#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv
from aws_lambda_powertools import Logger
from mypy_boto3_sesv2.type_defs import ListEmailIdentitiesResponseTypeDef, IdentityInfoTypeDef, \
    GetEmailIdentityPoliciesResponseTypeDef
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler
from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session


class SimpleEmailServiceV2:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('sesv2', credentials=account_credentials, region=region)
        self.ses_client = boto_session.get_client()

    @service_exception_handler
    def list_email_identities(self) -> list[IdentityInfoTypeDef]:
        response: ListEmailIdentitiesResponseTypeDef = self.ses_client.list_email_identities()

        identities = response.get('EmailIdentities', [])
        next_token = response.get('NextToken', None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.ses_client.list_email_identities(
                NextToken=next_token
            )
            self.logger.info("Extending Email Identities List")
            identities.extend(response.get('EmailIdentities', []))
            next_token = response.get('NextToken', None)

        return identities

    @resource_not_found_exception_handler
    def get_email_identity_policies(self, email_identity: str) -> GetEmailIdentityPoliciesResponseTypeDef:
        response: GetEmailIdentityPoliciesResponseTypeDef = self.ses_client.get_email_identity_policies(
            EmailIdentity=email_identity
        )
        self.logger.debug(f"Identity Policies: {response}")
        return response
