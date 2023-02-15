# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json

import boto3
from aws_lambda_powertools import Logger
from moto import mock_cloudformation, mock_sts

from resource_based_policy.step_functions_lambda.scan_cloudformation_stack_policy import CloudFormationStackPolicy
from tests.test_resource_based_policy.mock_data import mock_policies, event

logger = Logger(level="info")


@mock_sts
@mock_cloudformation
def test_cloudformation_stacks_no_stacks():
    # ACT
    response = CloudFormationStackPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


MOCK_TEMPLATE = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Description": "Stack 1",
    "Resources": {
        "EC2Instance1": {
            "Type": "AWS::EC2::Instance",
            "Properties": {
                "ImageId": "ami-12c6146b",
                "KeyName": "mock",
                "InstanceType": "t2.micro",
                "Tags": [
                    {"Key": "Description", "Value": "Test tag"},
                    {"Key": "Name", "Value": "Name tag for tests"},
                ],
            },
        }
    },
}


@mock_sts
@mock_cloudformation
def test_cloudformation_policy_scan():
    # ARRANGE
    for region in event['Regions']:
        cloudformation_client = boto3.client("cloudformation", region_name=region)
        for policy_object in mock_policies:
            if policy_object.get('MockResourceName'):
                cloudformation_client.create_stack(
                    StackName=policy_object.get('MockResourceName'),
                    TemplateBody=json.dumps(MOCK_TEMPLATE)
                )
                if policy_object.get('MockPolicy'):
                    cloudformation_client.set_stack_policy(
                        StackName=policy_object.get('MockResourceName'),
                        StackPolicyBody=json.dumps(policy_object.get('MockPolicy')))

    # ACT
    response = CloudFormationStackPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 12
    for resource in response:
        assert resource['DependencyType'] in [
            'aws:PrincipalOrgID',
            'aws:PrincipalOrgPaths',
            'aws:ResourceOrgID',
            'aws:ResourceOrgPaths'
        ]


@mock_sts
@mock_cloudformation
def test_cloudformation_policy_scan_with_filter_deleted_stacks():
    # ARRANGE
    for region in event['Regions']:
        cloudformation_client = boto3.client("cloudformation", region_name=region)
        delete_count = 3
        count = 0
        for policy_object in mock_policies:
            if policy_object.get('MockResourceName'):
                cloudformation_client.create_stack(
                    StackName=policy_object.get('MockResourceName'),
                    TemplateBody=json.dumps(MOCK_TEMPLATE)
                )
                if policy_object.get('MockPolicy'):
                    cloudformation_client.set_stack_policy(
                        StackName=policy_object.get('MockResourceName'),
                        StackPolicyBody=json.dumps(policy_object.get('MockPolicy')))

            if count < delete_count:
                cloudformation_client.delete_stack(
                    StackName=policy_object.get('MockResourceName')
                )
            count += 1

    # ACT
    response = CloudFormationStackPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 6
    for resource in response:
        assert resource['DependencyType'] in [
            'aws:PrincipalOrgID',
            'aws:PrincipalOrgPaths',
            'aws:ResourceOrgID',
            'aws:ResourceOrgPaths'
        ]
