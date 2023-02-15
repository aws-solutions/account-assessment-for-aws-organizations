# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import io
import zipfile

import boto3
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError
from moto import mock_lambda, mock_sts

from resource_based_policy.step_functions_lambda.scan_lambda_function_policy import LambdaFunctionPolicy
from tests.test_resource_based_policy.mock_data import event

logger = Logger(level="info")


@mock_sts
@mock_lambda
def test_lambda_function_policy_no_functions():
    # ACT
    response = LambdaFunctionPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_sts
@mock_lambda
def test_lambda_function_default_policy_scan(iam_client):
    # ARRANGE
    for region in event['Regions']:
        lambda_function_client = boto3.client("lambda", region_name=region)
        zip_content = get_test_zip_file1()
        function_name = "function-default-policy"
        lambda_function_client.create_function(
                FunctionName=function_name,
                Runtime="python3.7",
                Role=get_role_name(iam_client),
                Handler="lambda_function.handler",
                Code={"ZipFile": zip_content},
            )

    # ACT
    response = LambdaFunctionPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0


@mock_sts
@mock_lambda
def test_lambda_function_organization_policy_scan(iam_client):
    # ARRANGE
    for region in event['Regions']:
        lambda_function_client = boto3.client("lambda", region_name=region)
        zip_content = get_test_zip_file1()
        function_name = "function-default-policy"
        lambda_function_client.create_function(
                FunctionName=function_name,
                Runtime="python3.7",
                Role=get_role_name(iam_client),
                Handler="lambda_function.handler",
                Code={"ZipFile": zip_content},
            )
        lambda_function_client.add_permission(
            FunctionName=function_name,
            StatementId="1",
            Action="lambda:ListTags",
            Principal="arn:aws:iam::999999999999:user/SomeUser",
            PrincipalOrgID='o-a1b2c3d4e5'
        )

    # ACT
    response = LambdaFunctionPolicy(event).scan()
    logger.info(response)

    # ASSERT
    for resource in response:
        assert resource['DependencyType'] in [
            'aws:PrincipalOrgID',
            'aws:PrincipalOrgPaths',
            'aws:ResourceOrgID',
            'aws:ResourceOrgPaths'
        ]


def _process_lambda(func_str):
    zip_output = io.BytesIO()
    zip_file = zipfile.ZipFile(zip_output, "w", zipfile.ZIP_DEFLATED)
    zip_file.writestr("lambda_functions.py", func_str)
    zip_file.close()
    zip_output.seek(0)
    return zip_output.read()


def get_test_zip_file1():
    mock_code = """
    def lambda_handler(event, context):
        print("custom log event")
        return event
    """
    return _process_lambda(mock_code)


def get_role_name(iam_client):
    try:
        return iam_client.get_role(RoleName="my-role")["Role"]["Arn"]
    except ClientError:
        return iam_client.create_role(
            RoleName="my-role",
            AssumeRolePolicyDocument="some policy",
            Path="/my-path/",
        )["Role"]["Arn"]

