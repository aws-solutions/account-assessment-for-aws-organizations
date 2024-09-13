#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import datetime

from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_efs.type_defs import FileSystemDescriptionTypeDef

import resource_based_policy.resource_based_policy_model as model
from resource_based_policy.step_functions_lambda.scan_elastic_file_system_policy import ElasticFileSystemPolicy
from tests.test_resource_based_policy.mock_data import event

logger = Logger(level="info")


@mock_aws
def test_no_efs():
    # ACT
    response = ElasticFileSystemPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0


@mock_aws
def test_mock_efs_scan_policy(mocker):
    # ARRANGE
    describe_file_systems_response: list[FileSystemDescriptionTypeDef] = [
        {
            "OwnerId": "owner_id",
            "CreationToken": "creation_token",
            "FileSystemId": "mock_file_system_id",
            "CreationTime": datetime.datetime.now(),
            "LifeCycleState": "available",
            "NumberOfMountTargets": 1,
            "SizeInBytes": {
                "Value": 111,
            },
            "PerformanceMode": "generalPurpose",
            "Tags": [{
                "Key": "tag_key",
                "Value": "tag_value",
            }],
        }
    ]

    describe_file_system_policy_response: model.DescribeFileSystemPolicyResponse = {
        "FileSystemId": "mock_file_system_id",
        "Policy": "{\"Version\":\"2012-10-17\",\"Id\":\"read-only-example-policy\",\"Statement\":[{"
                  "\"Sid\":\"efs-statement-example\",\"Effect\":\"Allow\",\"Principal\":{"
                  "\"AWS\":\"arn:aws:iam::*:role/EfsReadOnly\"},\"Action\":[\"elasticfilesystem:ClientMount\"],"
                  "\"Condition\":{\"StringEquals\":{\"aws:PrincipalOrgID\":\"o-abcd1234\"}}}]}"}

    mock_elastic_file_systems(mocker,
                              describe_file_systems_response,
                              describe_file_system_policy_response)

    # ACT
    response = ElasticFileSystemPolicy(event).scan()
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


def mock_elastic_file_systems(mocker,
                              describe_file_systems_response=None,
                              describe_file_system_policy_response=None):

    # ARRANGE
    if describe_file_systems_response is None:
        describe_file_systems_response = []

    if describe_file_system_policy_response is None:
        describe_file_system_policy_response = []

    def mock_describe_file_systems(self):
        return describe_file_systems_response

    mocker.patch(
        "aws.services.elastic_file_system.ElasticFileSystem.describe_file_systems",
        mock_describe_file_systems
    )

    def mock_describe_file_system_policy(self, file_system_id):
        return describe_file_system_policy_response

    mocker.patch(
        "aws.services.elastic_file_system.ElasticFileSystem.describe_file_system_policy",
        mock_describe_file_system_policy
    )
