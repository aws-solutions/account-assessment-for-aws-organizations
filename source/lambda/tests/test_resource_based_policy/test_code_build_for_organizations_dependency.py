# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json

import boto3
from aws_lambda_powertools import Logger

from resource_based_policy.step_functions_lambda.scan_policy_all_services import CodeBuildResourcePolicy
from moto import mock_sts, mock_codebuild
from moto.core import DEFAULT_ACCOUNT_ID as ACCOUNT_ID
from tests.test_resource_based_policy.mock_data import event, mock_policies

logger = Logger(loglevel="info")


# @mock_sts
# @mock_codebuild
# def test_no_codebuild_keys():
#     # ACT
#     response = CodeBuildResourcePolicy(event).scan()
#     logger.info(response)
#
#     # ASSERT
#     assert len(list(response)) == 0
#

# @mock_sts
# @mock_codebuild
# def test_codebuild_key_no_policy():
#     # ARRANGE
#     name = "project_name"
#     source = {
#         "type": "S3",
#         "location": "bucket_name/path/file.zip"
#     }
#     # output artifacts
#     artifacts = {
#         "type": "S3",
#         "location": "bucket_name"
#     }
#     environment = {
#         "type": "LINUX_CONTAINER",
#         "image": "contents_not_validated",
#         "computeType": "BUILD_GENERAL1_SMALL"
#     }
#     service_role = f"arn:aws:iam::{ACCOUNT_ID}:role/service-role/my-codebuild-service-role"
#
#     for region in event['Regions']:
#         codebuild_client = boto3.client("codebuild", region_name=region)
#
#         codebuild_client.create_project(
#             name=name,
#             source=source,
#             artifacts=artifacts,
#             environment=environment,
#             serviceRole=service_role,
#         )
#
#     # ACT
#     response = CodeBuildResourcePolicy(event).scan()
#     logger.info(response)
#
#     # ASSERT
#     assert len(list(response)) == 0
