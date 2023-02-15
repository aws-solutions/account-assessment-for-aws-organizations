# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from moto import mock_sts
from mypy_boto3_serverlessrepo.type_defs import ApplicationSummaryTypeDef, ApplicationPolicyStatementTypeDef

from tests.test_resource_based_policy.mock_data import event
from resource_based_policy.step_functions_lambda.scan_serverless_application_policy import ServerlessApplicationPolicy

logger = Logger(level="info", service="test_code_build")


@mock_sts
def test_mock_serverless_application_repository_scan_policy_no_policies(mocker):
    # ARRANGE
    mock_serverless_application_repository(mocker)

    # ARRANGE
    response = ServerlessApplicationPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_sts
def test_mock_serverless_application_repository_scan_policy(mocker):
    # ARRANGE
    list_applications_response: list[ApplicationSummaryTypeDef] = [
        {
            'ApplicationId': 'app_1',
            'Author': 'user_1',
            'CreationTime': 'string',
            'Description': 'string',
            'HomePageUrl': 'string',
            'Labels': [
                'string',
            ],
            'Name': 'app_name',
            'SpdxLicenseId': 'string'
        },
    ]

    get_application_policy_response: list[ApplicationPolicyStatementTypeDef] = [
        {
            'Actions': [
                'GetApplication',
                'CreateCloudFormationTemplate'
            ],
            'PrincipalOrgIDs': [
                'o-a1b2c3d4e5',
            ],
            'Principals': [
                'account-id-1',
                'account-id-2',
            ],
            'StatementId': 'sid-1'
        },
    ]

    mock_serverless_application_repository(mocker,
                                           list_applications_response,
                                           get_application_policy_response)

    # ACT
    response = ServerlessApplicationPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 2
    for resource in response:
        assert resource["DependencyType"] in [
            "aws:PrincipalOrgID",
            "aws:PrincipalOrgPaths",
            "aws:ResourceOrgID",
            "aws:ResourceOrgPaths"
        ]


def mock_serverless_application_repository(mocker,
                                           list_applications_response=None,
                                           get_application_policy_response=None):

    # ARRANGE
    if list_applications_response is None:
        list_applications_response = []

    if get_application_policy_response is None:
        get_application_policy_response = []

    def mock_list_applications(self):
        return list_applications_response

    mocker.patch(
        "aws.services.serverless_application_repository.ServerlessApplicationRepository.list_applications",
        mock_list_applications
    )

    def mock_get_application_policy(self, application_id):
        return get_application_policy_response

    mocker.patch(
        "aws.services.serverless_application_repository.ServerlessApplicationRepository.get_application_policy",
        mock_get_application_policy
    )
