#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_codebuild.type_defs import ProjectTypeDef, GetResourcePolicyOutputTypeDef

from resource_based_policy.step_functions_lambda.scan_code_build_resource_policy import CodeBuildResourcePolicy
from tests.test_resource_based_policy.mock_data import event

logger = Logger(level='info', service="test_code_build")


@mock_aws
def test_mock_codebuild_scan_policy_no_projects(mocker):
    # ARRANGE
    mock_codebuild(mocker)

    # ARRANGE
    response = CodeBuildResourcePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_aws
def test_mock_codebuild_scan_policy(mocker):
    # ARRANGE
    list_projects_response: list[str] = ['test-codebuild-project']
    list_report_groups_response: list[str] = ['arn:aws:codebuild:us-east-1:999999999999:report-group/test-report-group']
    batch_get_projects_response: list[ProjectTypeDef] = [
        {
            'name': 'test-codebuild-project',
            'arn': 'arn:aws:codebuild:us-east-1:999999999999:project/test-codebuild-project',
            'source': {},
            'secondarySources': [],
            'secondarySourceVersions': [],
            'artifacts': {'type': 'NO_ARTIFACTS'},
            'secondaryArtifacts': [],
            'cache': {'type': 'NO_CACHE'},
            'environment': {'type': 'LINUX_CONTAINER', 'image': 'aws/codebuild/standard:6.0',
                            'computeType': 'BUILD_GENERAL1_SMALL', 'environmentVariables': [],
                            'privilegedMode': False, 'imagePullCredentialsType': 'CODEBUILD'},
            'serviceRole':
                'arn:aws:iam::999999999999:role/service-role/codebuild-test-codebuild-service'
                '-role',
            'timeoutInMinutes': 60,
            'queuedTimeoutInMinutes': 480,
            'encryptionKey': 'arn:aws:kms:us-east-1:999999999999:alias/aws/s3',
            'tags': [],
            'badge': {'badgeEnabled': False},
            'logsConfig': {'cloudWatchLogs': {'status': 'ENABLED'},
                           's3Logs': {'status': 'DISABLED',
                                      'encryptionDisabled': False}
                           },
            'projectVisibility': 'PRIVATE'
        }
    ]
    get_resource_policy_response: GetResourcePolicyOutputTypeDef = {
        "policy": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"CodeStarNotificationsPowerUserAccess\","
                  "\"Effect\":\"Allow\",\"Action\":[\"codestar-notifications:DescribeNotificationRule\"],"
                  "\"Resource\":\"*\",\"Condition\":{\"StringEquals\":{\"aws:PrincipalOrgID\":\"o-a1b2c3d4e5\"}}}]}",
        "ResponseMetadata": {
            "RequestId": "request_id",
            "HostId": "host_id",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {"mock_key": "mock_value"},
            "RetryAttempts": 3,
        }
    }

    mock_codebuild(mocker,
                   list_projects_response,
                   list_report_groups_response,
                   batch_get_projects_response,
                   get_resource_policy_response)

    # ACT
    response = CodeBuildResourcePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 4
    for resource in response:
        assert resource['DependencyType'] in [
            'aws:PrincipalOrgID',
            'aws:PrincipalOrgPaths',
            'aws:ResourceOrgID',
            'aws:ResourceOrgPaths',
            'aws:SourceOrgID',
            'aws:SourceOrgPaths'
        ]


def mock_codebuild(mocker,
                   list_projects_response=None,
                   list_report_groups_response=None,
                   batch_get_projects_response=None,
                   get_resource_policy_response=None):

    # ARRANGE
    if list_projects_response is None:
        list_projects_response = []
    if list_report_groups_response is None:
        list_report_groups_response = []
    if batch_get_projects_response is None:
        batch_get_projects_response = []
    if get_resource_policy_response is None:
        get_resource_policy_response = []

    def mock_list_projects(self):
        return list_projects_response

    mocker.patch(
        "aws.services.code_build.CodeBuild.list_projects",
        mock_list_projects
    )

    def mock_list_report_groups(self):
        return list_report_groups_response

    mocker.patch(
        "aws.services.code_build.CodeBuild.list_report_groups",
        mock_list_report_groups
    )

    def mock_batch_get_projects(self, names):
        return batch_get_projects_response

    mocker.patch(
        "aws.services.code_build.CodeBuild.batch_get_projects",
        mock_batch_get_projects
    )

    def mock_get_resource_policy(self, resource_arn: str):
        return get_resource_policy_response

    mocker.patch(
        "aws.services.code_build.CodeBuild.get_resource_policy",
        mock_get_resource_policy
    )
