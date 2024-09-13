#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_glacier.type_defs import DescribeVaultOutputTypeDef, VaultAccessPolicyTypeDef

from resource_based_policy.step_functions_lambda.scan_glacier_vault_policy import GlacierVaultPolicy
from tests.test_resource_based_policy.mock_data import event

logger = Logger(level="info")


@mock_aws
def test_glacier_vault_policy_scan_no_vaults():
    # ACT
    response = GlacierVaultPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_aws
def test_mock_glacier_scan_policy(mocker):
    # ARRANGE
    list_vaults_response: list[DescribeVaultOutputTypeDef] = [
        {
            "VaultARN": "arn:vault_name",
            "VaultName": "vault_name",
            "CreationDate": "date_time",
            "LastInventoryDate": "date_time",
            "NumberOfArchives": 1,
            "SizeInBytes": 10
        }
    ]

    get_vault_access_policy_response: VaultAccessPolicyTypeDef = {
        "Policy": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":["
                  "\"glacier:Delete*\"],\"Resource\":["
                  "\"arn:aws:glacier:us-west-2:999999999999:vaults/examplevault\"],\"Condition\":{\"StringEquals\":{"
                  "\"aws:PrincipalOrgID\":\"o-abcd1234\"}}}]}"
    }

    mock_glacier_vault(mocker,
                       list_vaults_response,
                       get_vault_access_policy_response)

    # ACT
    response = GlacierVaultPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 1
    for resource in response:
        assert resource["DependencyType"] in [
            "aws:PrincipalOrgID",
            "aws:PrincipalOrgPaths",
            "aws:ResourceOrgID",
            "aws:ResourceOrgPaths"
        ]


def mock_glacier_vault(mocker,
                       list_vaults_response=None,
                       get_vault_access_policy_response=None):

    # ARRANGE
    def mock_list_vaults(self):
        return list_vaults_response

    mocker.patch(
        "aws.services.s3.Glacier.list_vaults",
        mock_list_vaults
    )

    def mock_get_vault_access_policy(self, vault_name):
        return get_vault_access_policy_response

    mocker.patch(
        "aws.services.s3.Glacier.get_vault_access_policy",
        mock_get_vault_access_policy
    )
