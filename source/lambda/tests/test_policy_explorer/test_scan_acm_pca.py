#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_acm_pca.type_defs import CertificateAuthorityTypeDef

from policy_explorer.policy_explorer_model import PolicyType
from policy_explorer.step_functions_lambda.scan_acm_pca_policy import ACMPCAPolicy
from tests.test_policy_explorer.mock_data import event

logger = Logger(level='info')


@mock_aws
def test_mock_acm_pca_scan_policy_no_policies(mocker):
    # Arrange
    mock_acm_pca(mocker)

    # Act
    response = ACMPCAPolicy(event).scan()
    logger.info(response)

    # Assert
    assert response == []


@mock_aws
def test_mock_acm_pca_scan_policy(mocker):
    # Arrange
    list_certificate_authorities_response: list[CertificateAuthorityTypeDef] = [
        {
            "Arn": "arn:aws:acm-pca:us-east-2:111122223333:certificate-authority/mycertificate"
        }
    ]
    
    mock_acm_pca(mocker, list_certificate_authorities_response=list_certificate_authorities_response, get_policy_response="")

    # ACT
    response = ACMPCAPolicy(event).scan()
    logger.info(f"RESPONSE: {len(response)}")

    # Assert
    assert len(response) == 4
    assert response[0]['PartitionKey'] == PolicyType.RESOURCE_BASED_POLICY.value
    assert response[3]['Condition'] == '{\"StringEquals\": {\"aws:PrincipalOrgID\": \"o-eci09zojnh\"}}'
    assert response[3]['Action'] == '[\"acm-pca:DescribeCertificateAuthority\", \"acm-pca:GetCertificate\", \"acm-pca:GetCertificateAuthorityCertificate\", \"acm-pca:ListPermissions\", \"acm-pca:ListTags\"]'

def mock_acm_pca(mocker, list_certificate_authorities_response=None, get_policy_response=None):
    if not list_certificate_authorities_response:
        list_certificate_authorities_response = []

    if not get_policy_response:
        get_policy_response = ""
    
    def mock_list_certificate_authorities(self):
        return list_certificate_authorities_response
    
    mocker.patch(
        "aws.services.acm_private_certificate_authority.ACMPCA.list_certificate_authorities",
        mock_list_certificate_authorities
    )

    def mock_get_policy(self, resource_arn: str):
        if (resource_arn == "arn:aws:acm-pca:us-east-2:111122223333:certificate-authority/mycertificate"):
            return "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"1\",\"Effect\":\"Allow\",\"Principal\": {\"AWS\":\"111122223333\"},\"Action\":\"acm-pca:IssueCertificate\",\"Resource\":\"arn:aws:acm-pca:us-east-2:111122223333:certificate-authority/mycertificate\",\"Condition\":{\"StringEquals\":{\"acm-pca:TemplateArn\":\"arn:aws:acm-pca:::template/EndEntityCertificate/V1\",\"aws:PrincipalOrgID\":\"o-eci09zojnh\"}}},{\"Sid\":\"1\",\"Effect\":\"Allow\",\"Principal\": {\"AWS\": \"111122223333\"},\"Action\":[\"acm-pca:DescribeCertificateAuthority\",\"acm-pca:GetCertificate\",\"acm-pca:GetCertificateAuthorityCertificate\",\"acm-pca:ListPermissions\",\"acm-pca:ListTags\"],\"Resource\":\"arn:aws:acm-pca:us-east-2:111122223333:certificate-authority/mycertificate\",\"Condition\":{\"StringEquals\":{\"aws:PrincipalOrgID\":\"o-eci09zojnh\"}}}]}"

        else:
            return {'Error': 'There is no policy for registry default. Create a resource-based policy and try your request again.'}
    mocker.patch(
            "aws.services.acm_private_certificate_authority.ACMPCA.get_policy",
            mock_get_policy
        )