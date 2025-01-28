# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_acm_pca.type_defs import CertificateAuthorityTypeDef
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn
import policy_explorer.policy_explorer_model as model
from aws.services.acm_private_certificate_authority import ACMPCA
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions 


class ACMPCAPolicy:
    def __init__(self, event:model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)
    
    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning ACM Private Certificate Authority Policies in {region}")
        acm_pca_client = ACMPCA(self.account_id, region)
        certificate_authorities: list[CertificateAuthorityTypeDef] = acm_pca_client.list_certificate_authorities()
        certificate_authorities_policy_details: list[model.PolicyDetails] = self._get_certificate_authorities_and_policies(certificate_authorities, acm_pca_client)
        self.logger.debug(f"Certificate Authorities and Policy Details {certificate_authorities_policy_details}")
        certificate_authorities_for_region = []
        for resource in certificate_authorities_policy_details:
            certificate_authorities_for_region.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(resource))
        self.logger.debug(f"Certificate Authorities with organization dependency {certificate_authorities_for_region}")
        return certificate_authorities_for_region
    
    def _get_certificate_authorities_and_policies(self, certificate_authorities: list[CertificateAuthorityTypeDef], acm_pca_client: ACMPCA):
        self.logger.debug(f"CERTIFICATE AUTHORITY VALUE: {str(certificate_authorities)}")
        return list(self._get_acm_pca_policy_details(certificate_authority, acm_pca_client) for certificate_authority in certificate_authorities)
    
    @staticmethod
    def _get_acm_pca_policy_details(certificate_authority: CertificateAuthorityTypeDef, acm_pca_client: ACMPCA)-> model.PolicyDetails:
        resource_arn = certificate_authority.get('Arn')
        certificate_authority_policy: str = acm_pca_client.get_policy(certificate_authority.get('Arn'))
        policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
        policy_details.update({'Policy': certificate_authority_policy})
        policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
        return policy_details