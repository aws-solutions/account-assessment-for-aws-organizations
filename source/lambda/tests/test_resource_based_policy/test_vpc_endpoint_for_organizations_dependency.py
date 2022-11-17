# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json

import boto3
from aws_lambda_powertools import Logger

from resource_based_policy.step_functions_lambda.scan_policy_all_services import VPCEndpointsPolicy
from moto import mock_sts, mock_ec2
from tests.test_resource_based_policy.mock_data import event, mock_policies

logger = Logger(loglevel="info")


@mock_sts
@mock_ec2
def test_no_vpc_endpoint():
    # ACT
    response = VPCEndpointsPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0


@mock_sts
@mock_ec2
def test_vpc_endpoint_no_policy():
    # ARRANGE
    for region in event['Regions']:
        ec2_client = boto3.client("ec2", region_name=region)
        vpc = ec2_client.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]

        vpc_end_point = ec2_client.create_vpc_endpoint(
            VpcId=vpc["VpcId"],
            ServiceName="com.amazonaws.us-east-1.s3",
            VpcEndpointType="Gateway",
        )["VpcEndpoint"]
        logger.info(f"VPC Endpoint: {vpc_end_point}")

    # ACT
    response = VPCEndpointsPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0


@mock_sts
@mock_ec2
def test_vpc_endpoint_with_policy():
    # ARRANGE
    for region in event['Regions']:
        ec2_client = boto3.client("ec2", region_name=region)
        vpc = ec2_client.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]
        for policy_object in mock_policies:
            # if no policy is present the topic is created with default policy
            if policy_object.get('MockPolicy'):
                vpc_end_point = ec2_client.create_vpc_endpoint(
                    VpcId=vpc["VpcId"],
                    ServiceName="com.amazonaws.us-east-1.s3",
                    VpcEndpointType="Gateway",
                    PolicyDocument=json.dumps(policy_object.get('MockPolicy'))
                )["VpcEndpoint"]
                logger.info(f"VPC Endpoint: {vpc_end_point}")

    # ACT
    response = VPCEndpointsPolicy(event).scan()
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
