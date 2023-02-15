# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json

import boto3
from aws_lambda_powertools import Logger
from moto import mock_sts, mock_kms

from resource_based_policy.step_functions_lambda.scan_key_management_service_policy import KeyManagementServicePolicy
from tests.test_resource_based_policy.mock_data import event, mock_policies

logger = Logger(level="info")


@mock_sts
@mock_kms
def test_no_kms_keys():
    # ACT
    response = KeyManagementServicePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0


@mock_sts
@mock_kms
def test_kms_key_no_policy():
    # ARRANGE
    for region in event['Regions']:
        client = boto3.client("kms", region_name=region)

        response = client.create_key(
            Description="my key",
            KeyUsage="ENCRYPT_DECRYPT",
            Tags=[{"TagKey": "project", "TagValue": "moto"}],
        )

    # ACT
    response = KeyManagementServicePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0


@mock_sts
@mock_kms
def test_kms_key_with_policy():
    # ARRANGE
    for region in event['Regions']:
        client = boto3.client("kms", region_name=region)

        myPolicy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "SNSPolicy",
                    "Effect": "Allow",
                    "Action": [
                        "SNS:GetTopicAttributes",
                        "SNS:SetTopicAttributes"
                    ],
                    "Resource": "arn:aws:sns:us-east-1:999999999999:MyNotifications",
                    "Condition": {
                        "StringEquals": {
                            "AWS:SourceOwner": "999999999999"
                        }
                    }
                },
                {
                    "Sid": "AWSSNSPolicy",
                    "Effect": "Allow",
                    "Action": "sns:Publish",
                    "Resource": "arn:aws:sns:us-east-1:999999999999:MyNotifications",
                    "Condition": {
                        "StringEquals": {
                            "aws:PrincipalOrgID": "o-a1b2c3d4e5"
                        }
                    }
                }
            ]
        }
        response = client.create_key(
            Policy=json.dumps(myPolicy),
            Description="my key",
            KeyUsage="ENCRYPT_DECRYPT",
            Tags=[{"TagKey": "project", "TagValue": "moto"}],
        )

    # ACT
    response = KeyManagementServicePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 2


@mock_sts
@mock_kms
def test_kms_policy_scan():
    # ARRANGE
    for region in event['Regions']:
        kms_client = boto3.client("kms", region_name=region)
        for policy_object in mock_policies:
            if policy_object.get('MockResourceName'):
                # if no policy is present the topic is created with default policy
                if policy_object.get('MockPolicy'):
                    response = kms_client.create_key(
                        Policy=json.dumps(policy_object.get('MockPolicy')),
                        Description=policy_object.get('MockResourceName'),
                        KeyUsage="ENCRYPT_DECRYPT",
                        Tags=[{"TagKey": "project", "TagValue": "moto"}])
                else:
                    response = kms_client.create_key(
                        Description=policy_object.get('MockResourceName'),
                        KeyUsage="ENCRYPT_DECRYPT")
                logger.info(f"Created Key: {response.get('KeyMetadata').get('KeyId')} for {policy_object.get('MockResourceName')} with "
                            f"policy {policy_object.get('MockPolicy')}")

    # ACT
    response = KeyManagementServicePolicy(event).scan()
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
