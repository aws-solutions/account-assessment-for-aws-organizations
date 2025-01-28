# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


from os import getenv


from aws_lambda_powertools import Logger
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler
from mypy_boto3_ssm_contacts.type_defs import GetContactPolicyResultTypeDef, ContactTypeDef
from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session


class SSMContacts:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('ssm-contacts', credentials=account_credentials, region=region)
        self.ssm_contacts_client = boto_session.get_client()
    
    @service_exception_handler
    def list_contacts(self) -> list[ContactTypeDef]:
        response: ContactTypeDef = self.ssm_contacts_client.list_contacts()

        contacts_list = response.get('Contacts', [])
        next_token = response.get('NextToken', None)
        
        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token}")
            response = self.ssm_contacts_client.list_contacts(
                NextToken=next_token
            )
            self.logger.info("Extending Contacts List")
            contacts_list.extend(response.get('Contacts', []))
            next_token = response.get('NextToken', None)

        return contacts_list
    
    @resource_not_found_exception_handler
    def get_contact_policy(self, contact_arn: str) -> str:
        response:  GetContactPolicyResultTypeDef = self.ssm_contacts_client.get_contact_policy(
            ContactArn=contact_arn
        )
        self.logger.debug(f"Contact Policy for {contact_arn}: {response}")
        return response.get('Policy') 