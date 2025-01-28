# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from os import getenv


from aws_lambda_powertools import Logger
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler
from mypy_boto3_acm_pca.type_defs import CertificateAuthorityTypeDef, GetPolicyResponseTypeDef
from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session

class ACMPCA:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('acm-pca', credentials=account_credentials, region=region)
        self.acm_pca_client = boto_session.get_client()
    
    @service_exception_handler
    def list_certificate_authorities(self) -> list[CertificateAuthorityTypeDef]:
        response: CertificateAuthorityTypeDef = self.acm_pca_client.list_certificate_authorities()

        certificate_authorities_list = response.get('CertificateAuthorities', [])
        next_token = response.get('NextToken', None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token}")
            response = self.acm_pca_client.list_certificate_authorities(
                NextToken=next_token
            )
            self.logger.info("Extending Certificate Authorities List")
            certificate_authorities_list.extend(response.get('CertificateAuthorities', []))
            next_token = response.get('NextToken', None)
        
        return certificate_authorities_list


    @resource_not_found_exception_handler
    def get_policy(self, resource_arn: str) -> str:
        response: GetPolicyResponseTypeDef = self.acm_pca_client.get_policy(
            ResourceArn=resource_arn
        )
        self.logger.debug(f"Certificate Authorities Policy for {resource_arn}: {response}")
        return response.get('Policy')