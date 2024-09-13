#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import datetime

from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_glue.type_defs import GluePolicyTypeDef

from resource_based_policy.step_functions_lambda.scan_glue_resource_policy import GlueResourcePolicy
from tests.test_resource_based_policy.mock_data import event

logger = Logger(level='info', service="test_code_build")


@mock_aws
def test_mock_glue_scan_policy_no_policies(mocker):
    # ARRANGE
    mock_glue(mocker)

    # ARRANGE
    response = GlueResourcePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_aws
def test_mock_glue_scan_policy(mocker):
    # ARRANGE
    get_resource_policies_response: list[GluePolicyTypeDef] = [{
        "PolicyInJson": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"glue:Get*\","
                        "\"glue:BatchGet*\"],\"Resource\":\"*\",\"Condition\":{\"StringEquals\":{"
                        "\"aws:PrincipalOrgID\":\"o-a1b2c3d4e5\"}}}]}",
        "PolicyHash": "policy_hash",
        "CreateTime": datetime.datetime.now(),
        "UpdateTime": datetime.datetime.now()
    }]

    mock_glue(mocker,
              get_resource_policies_response)

    # ACT
    response = GlueResourcePolicy(event).scan()
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


def mock_glue(mocker,
              get_resource_policies_response=None):

    # ARRANGE
    if get_resource_policies_response is None:
        get_resource_policies_response = []

    def mock_get_resource_policies(self):
        return get_resource_policies_response

    mocker.patch(
        "aws.services.glue.Glue.get_resource_policies",
        mock_get_resource_policies
    )
