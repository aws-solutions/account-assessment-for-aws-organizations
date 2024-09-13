#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_sesv2.type_defs import IdentityInfoTypeDef, GetEmailIdentityPoliciesResponseTypeDef

from resource_based_policy.step_functions_lambda.scan_ses_identity_policy import SESIdentityPolicy
from tests.test_resource_based_policy.mock_data import event

logger = Logger(level='info', service="test_code_build")


@mock_aws
def test_mock_ses_scan_policy_no_policies(mocker):
    # ARRANGE
    mock_ses(mocker)

    # ARRANGE
    response = SESIdentityPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_aws
def test_mock_ses_scan_policy(mocker):
    # ARRANGE
    list_email_identities_response: list[IdentityInfoTypeDef] = [
            {
                "IdentityType": "EMAIL_ADDRESS",
                "IdentityName": "example@example.com",
                "SendingEnabled": True,
                "VerificationStatus": "SUCCESS"
            },
        ]

    get_email_identity_policies_response: GetEmailIdentityPoliciesResponseTypeDef = {
        "Policies": {
            "PolicyName": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":["
                          "\"ses:SendEmail\",\"ses:SendRawEmail\"],\"Resource\":\"*\",\"Condition\":{"
                          "\"StringEquals\":{\"aws:PrincipalOrgID\":\"o-a1b2c3d4e5\"}}}]}"
        },
        "ResponseMetadata": {
            "RequestId": "request_id",
            "HostId": "host_id",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {"mock_key": "mock_value"},
            "RetryAttempts": 3,
        }
    }

    mock_ses(mocker,
             list_email_identities_response,
             get_email_identity_policies_response)

    # ACT
    response = SESIdentityPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 2
    for resource in response:
        assert resource['DependencyType'] in [
            'aws:PrincipalOrgID',
            'aws:PrincipalOrgPaths',
            'aws:ResourceOrgID',
            'aws:ResourceOrgPaths',
            'aws:SourceOrgID',
            'aws:SourceOrgPaths'
        ]


def mock_ses(mocker,
             list_email_identities_response=None,
             get_email_identity_policies_response=None):

    # ARRANGE
    if list_email_identities_response is None:
        list_email_identities_response = []

    if get_email_identity_policies_response is None:
        get_email_identity_policies_response = []

    def mock_list_email_identities(self):
        return list_email_identities_response

    mocker.patch(
        "aws.services.simple_email_service_v2.SimpleEmailServiceV2.list_email_identities",
        mock_list_email_identities
    )

    def mock_get_email_identity_policies(self, email_identity: str):
        return get_email_identity_policies_response

    mocker.patch(
        "aws.services.simple_email_service_v2.SimpleEmailServiceV2.get_email_identity_policies",
        mock_get_email_identity_policies
    )
