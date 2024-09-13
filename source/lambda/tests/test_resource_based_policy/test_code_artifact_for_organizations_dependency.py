#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import datetime

from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_codeartifact.type_defs import DomainSummaryTypeDef, RepositorySummaryTypeDef, \
    GetDomainPermissionsPolicyResultTypeDef, GetRepositoryPermissionsPolicyResultTypeDef

from resource_based_policy.step_functions_lambda.scan_code_artifact_policy import CodeArtifactPolicy
from tests.test_resource_based_policy.mock_data import event

logger = Logger(level='info', service="test_code_build")


@mock_aws
def test_mock_codeartifact_scan_policy_no_projects(mocker):
    # ARRANGE
    mock_codeartifact(mocker)

    # ARRANGE
    response = CodeArtifactPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_aws
def test_mock_codeartifact_scan_policy(mocker):
    # ARRANGE
    list_domains_response: list[DomainSummaryTypeDef] = [{
        "name": "mock_domain_name",
        "owner": "aws",
        "arn": "arn:aws:codeartifact:us-east-1:999999999999:domain/mock_domain_name",
        "status": "Active",
        "createdTime": datetime.datetime.now(),
        "encryptionKey": "mock_key",
    }]
    list_repositories_response: list[RepositorySummaryTypeDef] = [
        {
            "name": "mock_repo_name",
            "administratorAccount": "999999999999",
            "domainName": "mock_domain_name",
            "domainOwner": "aws",
            "arn": "arn:aws:codeartifact:us-east-1:999999999999:repository/mock_domain_name/mock_repo_name",
            "description": "mock repo",
        }
    ]
    get_domain_permissions_policy_response: GetDomainPermissionsPolicyResultTypeDef = {
        "policy": {
            "resourceArn": "arn:aws:codeartifact:us-east-1:999999999999:domain/mock_domain_name",
            "revision": "1",
            "document": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"ContributorPolicy\","
                        "\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":[\"codeartifact:CreateRepository\","
                        "\"codeartifact:DescribeDomain\",\"codeartifact:GetAuthorizationToken\","
                        "\"codeartifact:GetDomainPermissionsPolicy\",\"codeartifact:ListRepositoriesInDomain\","
                        "\"sts:GetServiceBearerToken\"],\"Resource\":\"*\",\"Condition\":{\"StringEquals\":{"
                        "\"aws:PrincipalOrgID\":\"o-a1b2c3d4e5\"}}}]}",
        },
        "ResponseMetadata": {
            "RequestId": "request_id",
            "HostId": "host_id",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {"mock_key": "mock_value"},
            "RetryAttempts": 3,
        }
    }
    get_repository_permissions_policy_response: GetRepositoryPermissionsPolicyResultTypeDef = {
        "policy": {
            "resourceArn": "arn:aws:codeartifact:us-east-1:999999999999:repository/mock_domain_name/mock_repo_name",
            "revision": "1",
            "document": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":\"*\","
                        "\"Action\":[\"codeartifact:DescribePackageVersion\",\"codeartifact:DescribeRepository\","
                        "\"codeartifact:ListPackageVersions\",\"codeartifact:ListPackages\"],\"Resource\":\"*\","
                        "\"Condition\":{\"StringEquals\":{\"aws:PrincipalOrgID\":\"o-a1b2c3d4e5\"}}}]}",
        },
        "ResponseMetadata": {
            "RequestId": "request_id",
            "HostId": "host_id",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {"mock_key": "mock_value"},
            "RetryAttempts": 3,
        }
    }

    mock_codeartifact(mocker,
                      list_domains_response,
                      list_repositories_response,
                      get_domain_permissions_policy_response,
                      get_repository_permissions_policy_response)

    # ACT
    response = CodeArtifactPolicy(event).scan()
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


def mock_codeartifact(mocker,
                      list_domains_response=None,
                      list_repositories_response=None,
                      get_domain_permissions_policy_response=None,
                      get_repository_permissions_policy_response=None):

    # ARRANGE
    if list_domains_response is None:
        list_domains_response = []
    if list_repositories_response is None:
        list_repositories_response = []
    if get_domain_permissions_policy_response is None:
        get_domain_permissions_policy_response = []
    if get_repository_permissions_policy_response is None:
        get_repository_permissions_policy_response = []

    def mock_list_domains(self):
        return list_domains_response

    mocker.patch(
        "aws.services.code_artifact.CodeArtifact.list_domains",
        mock_list_domains
    )

    def mock_list_repositories(self):
        return list_repositories_response

    mocker.patch(
        "aws.services.code_artifact.CodeArtifact.list_repositories",
        mock_list_repositories
    )

    def mock_get_domain_permissions_policy(self, domain_name: str):
        return get_domain_permissions_policy_response

    mocker.patch(
        "aws.services.code_artifact.CodeArtifact.get_domain_permissions_policy",
        mock_get_domain_permissions_policy
    )

    def mock_get_repository_permissions_policy(self, domain_name: str, repository_name: str):
        return get_repository_permissions_policy_response

    mocker.patch(
        "aws.services.code_artifact.CodeArtifact.get_repository_permissions_policy",
        mock_get_repository_permissions_policy
    )
