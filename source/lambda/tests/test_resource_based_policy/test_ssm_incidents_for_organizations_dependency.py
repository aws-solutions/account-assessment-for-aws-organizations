# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from moto import mock_sts
from mypy_boto3_ssm_incidents.type_defs import ResponsePlanSummaryTypeDef, \
    ResourcePolicyTypeDef

from resource_based_policy.step_functions_lambda.scan_ssm_incidents_response_plan_policy import \
    SSMIncidentsResponsePlanPolicy
from tests.test_resource_based_policy.mock_data import event

logger = Logger(level='info', service="test_code_build")


@mock_sts
def test_mock_ssm_incidents_scan_policy_no_policies(mocker):
    # ARRANGE
    mock_ssm_incidents(mocker)

    # ARRANGE
    response = SSMIncidentsResponsePlanPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_sts
def test_mock_ssm_incidents_scan_policy(mocker):
    # ARRANGE
    list_response_plans_response: list[ResponsePlanSummaryTypeDef] = [
        {
            "arn": "arn:aws:ssm-incidents::111122223333:response-plan/myplan",
            "name": "example-response",
        }
    ]

    get_resource_policies_response: list[ResourcePolicyTypeDef] = [
        {
            "policyDocument": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"OrganizationAccess\","
                              "\"Effect\":\"Allow\",\"Principal\":\"*\",\"Condition\":{\"StringEquals\":{"
                              "\"aws:PrincipalOrgID\":\"o-abc123def45\"}},\"Action\":["
                              "\"ssm-incidents:GetResponsePlan\",\"ssm-incidents:StartIncident\","
                              "\"ssm-incidents:UpdateIncidentRecord\",\"ssm-incidents:GetIncidentRecord\","
                              "\"ssm-incidents:CreateTimelineEvent\",\"ssm-incidents:UpdateTimelineEvent\","
                              "\"ssm-incidents:GetTimelineEvent\",\"ssm-incidents:ListTimelineEvents\","
                              "\"ssm-incidents:UpdateRelatedItems\",\"ssm-incidents:ListRelatedItems\"],"
                              "\"Resource\":[\"arn:aws:ssm-incidents:*:111122223333:response-plan/myplan\","
                              "\"arn:aws:ssm-incidents:*:111122223333:incident-record/myplan/*\"]}]}",
            "policyId": "mock_policy_id",
            "ramResourceShareRegion": "us-east-1",
        }
    ]

    mock_ssm_incidents(mocker,
                       list_response_plans_response,
                       get_resource_policies_response)

    # ACT
    response = SSMIncidentsResponsePlanPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 2
    for resource in response:
        assert resource['DependencyType'] in [
            'aws:PrincipalOrgID',
            'aws:PrincipalOrgPaths',
            'aws:ResourceOrgID',
            'aws:ResourceOrgPaths'
        ]


def mock_ssm_incidents(mocker,
                       list_response_plans_response=None,
                       get_resource_policies_response=None):

    # ARRANGE
    if list_response_plans_response is None:
        list_response_plans_response = []

    if get_resource_policies_response is None:
        get_resource_policies_response = []

    def mock_list_response_plans(self):
        return list_response_plans_response

    mocker.patch(
        "aws.services.ssm_incidents.SSMIncidents.list_response_plans",
        mock_list_response_plans
    )

    def mock_get_resource_policies(self, resource_arn: str):
        return get_resource_policies_response

    mocker.patch(
        "aws.services.ssm_incidents.SSMIncidents.get_resource_policies",
        mock_get_resource_policies
    )
