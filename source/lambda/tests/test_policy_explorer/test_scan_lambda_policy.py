#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import io
import zipfile

import boto3
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError
from moto import mock_aws

from policy_explorer.policy_explorer_model import PolicyType, PolicyDetails
from policy_explorer.step_functions_lambda.scan_lambda_function_policy import LambdaFunctionPolicy
from tests.test_policy_explorer.mock_data import event

logger = Logger(level="info")


@mock_aws
def test_lambda_function_policy_no_functions():
    # ACT
    response = LambdaFunctionPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_aws
def test_lambda_function_default_policy_scan(mocker, iam_client):
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

    def mock_get_policy_details_from_arn(resource_arn: str):
        return PolicyDetails(
            PolicyType=None,
            Region="us-east-1",
            AccountId=999999999999,
            Service="lambda",
            ResourceIdentifier="function-name",
            Policy=None
        )
    mocker.patch(
        "policy_explorer.step_functions_lambda.scan_lambda_function_policy.get_policy_details_from_arn",
        mock_get_policy_details_from_arn
    )
    # ACT
    response = LambdaFunctionPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0


@mock_aws
def test_lambda_function_organization_policy_scan(mocker, iam_client):
    # ARRANGE
    for region in event['Regions']:
        lambda_function_client = boto3.client("lambda", region_name=region)
        zip_content = get_test_zip_file1()
        function_name = "function-default-policy"

        lambda_function_client.add_permission(
            FunctionName=function_name,
            StatementId="1",
            Action="lambda:ListTags",
            Principal="arn:aws:iam::999999999999:user/SomeUser",
            PrincipalOrgID='o-a1b2c3d4e5'
        )
    def mock_get_policy_details_from_arn(resource_arn: str):
        return PolicyDetails(
            PolicyType=None,
            Region="us-east-1",
            AccountId=999999999999,
            Service="lambda",
            ResourceIdentifier="function-name",
            Policy=None
        )
    mocker.patch(
        "policy_explorer.step_functions_lambda.scan_lambda_function_policy.get_policy_details_from_arn",
        mock_get_policy_details_from_arn
    )
    
    def mock_get_policy(arg1: str, function_name: str):
        logger.info(arg1)
        logger.info(function_name)
        return {"Policy":"{\"Version\":\"2012-10-17\",\"Id\":\"default\",\"Statement\":[{\"Sid\":\"StackSet-account-assessment-14ba7782-f201-4-ApiAccountAssessmentForAWSOrganisationsApid-flUBFfVaA0f3\",\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"apigateway.amazonaws.com\"},\"Action\":\"lambda:InvokeFunction\",\"Resource\":\"arn:aws:lambda:us-east-2:111111111111:function:StackSet-account-assessme-DelegatedAdminsRead591DC-rhv1zfo76L1z\",\"Condition\":{\"ArnLike\":{\"AWS:SourceArn\":\"arn:aws:execute-api:us-east-2:111111111111:p2ut8bkpyi/test-invoke-stage/GET/delegated-admins\"}}},{\"Sid\":\"StackSet-account-assessment-14ba7782-f201-4-ApiAccountAssessmentForAWSOrganisationsApid-vVq9XsCs32U2\",\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"apigateway.amazonaws.com\"},\"Action\":\"lambda:InvokeFunction\",\"Resource\":\"arn:aws:lambda:us-east-2:111111111111:function:StackSet-account-assessme-DelegatedAdminsRead591DC-rhv1zfo76L1z\",\"Condition\":{\"ArnLike\":{\"AWS:SourceArn\":\"arn:aws:execute-api:us-east-2:111111111111:p2ut8bkpyi/prod/GET/delegated-admins\"}}}]}"}
    
    mocker.patch(
        "aws.services.lambda_functions.LambdaFunctions.get_policy",
        mock_get_policy
    )
    # ACT
    response = LambdaFunctionPolicy(event).scan()
    logger.info(response)
    
    assert len(list(response)) == 4

    # ASSERT
    for resource in response:
        assert resource.get('PartitionKey') == PolicyType.RESOURCE_BASED_POLICY.value

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

