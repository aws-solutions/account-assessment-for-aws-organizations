#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn

arns = [
    "arn:aws:codeartifact:us-east-2:111111111111:repository/test-for-aa/test-for-aa-repo",
    "arn:aws:codeartifact:us-east-2:111111111111:domain/test-for-aa",
    "arn:aws:codebuild:us-east-2:111111111111:project/DeployProject1CF7CB79-op2vIHtB6L9C",
    "arn:aws:codebuild:us-east-2:111111111111:report-groups/test",
    "arn:aws:config:us-west-2:111111111111:organization-config-rule/ec2-no-amazon-key-pair-yvylwqkv",
    "arn:aws:ecr:us-west-2:111111111111:repository/test-for-aa",
    "arn:aws:elasticfilesystem:us-west-2:111111111111:file-system/fs-0a01aff58d514cc4f",
    "arn:aws:schemas:us-west-2:111111111111:registry/default",
    "arn:aws:glacier:us-east-2:111111111111:vaults/test-for-aa",
    "arn:aws:iam::111111111111:role/role-name/AssumeRolePolicyDocument",
    "arn:aws:iam::111111111111:policy/service-role/AmazonSageMakerServiceCatalogProductsUseRole-20231004T094891"
    ]

    
def test_get_policy_details_from_arn_with_empty_region():
    arn = "arn:aws:ssm-incidents::111111111111:incident-record/dfdf/34c57e00-19d3-ee2e-6a0d-9344a03cadc5"
    policy_details = get_policy_details_from_arn(arn)
    assert policy_details.get("AccountId") == "111111111111"
    assert policy_details.get("Service") == "ssm-incidents"
    assert policy_details.get("ResourceIdentifier") == "incident-record/dfdf/34c57e00-19d3-ee2e-6a0d-9344a03cadc5"
    assert policy_details.get("Region") == ""
    assert policy_details.get("PolicyType") == None
    assert policy_details.get("Policy") == None

def test_get_policy_details_from_arn():
    arn = "arn:aws:acm-pca:us-east-2:111111111111:certificate-authority/942cc890-3671-485f-87e3-a52a39c77591"
    policy_details = get_policy_details_from_arn(arn)
    assert policy_details.get("AccountId") == "111111111111"
    assert policy_details.get("Service") == "acm-pca"
    assert policy_details.get("ResourceIdentifier") == "certificate-authority/942cc890-3671-485f-87e3-a52a39c77591"
    assert policy_details.get("Region") == "us-east-2"
    assert policy_details.get("PolicyType") == None
    assert policy_details.get("Policy") == None
    
def test_get_policy_details_from_arn_for_s3_arn():
    
    arn = "arn:aws:s3:::aa-files-to-download"
    policy_details = get_policy_details_from_arn(arn)
    assert policy_details.get("AccountId") == ""
    assert policy_details.get("Service") == "s3"
    assert policy_details.get("ResourceIdentifier") == "aa-files-to-download"
    assert policy_details.get("Region") == ""
    assert policy_details.get("PolicyType") == None
    assert policy_details.get("Policy") == None
    
def test_get_policy_details_from_arn_for_rest_apis():
    
    arn = "arn:aws:apigateway:us-east-1::/restapis/p1jdh44"
    
    policy_details = get_policy_details_from_arn(arn)
    assert policy_details.get("AccountId") == ""
    assert policy_details.get("Service") == "apigateway"
    assert policy_details.get("ResourceIdentifier") == "/restapis/p1jdh44"
    assert policy_details.get("Region") == "us-east-1"
    assert policy_details.get("PolicyType") == None
    assert policy_details.get("Policy") == None
    
def test_get_policy_details_from_arn_for_backup_vault():
    
    arn = "arn:aws:backup:us-east-2:111111111111:backup-vault:test"
    policy_details = get_policy_details_from_arn(arn)
    assert policy_details.get("AccountId") == "111111111111"
    assert policy_details.get("Service") == "backup"
    assert policy_details.get("ResourceIdentifier") == "backup-vault:test"
    assert policy_details.get("Region") == "us-east-2"
    assert policy_details.get("PolicyType") == None
    assert policy_details.get("Policy") == None
    
def test_get_policy_details_from_arn_for_cloudformation_stack():
    arn = "arn:aws:cloudformation:us-east-2:111111111111:stack/ntfw-1/554e2ff0-5e0c-11ee-a468-022237916e0b"
    policy_details = get_policy_details_from_arn(arn)
    assert policy_details.get("AccountId") == "111111111111"
    assert policy_details.get("Service") == "cloudformation"
    assert policy_details.get("ResourceIdentifier") == "stack/ntfw-1/554e2ff0-5e0c-11ee-a468-022237916e0b"
    assert policy_details.get("Region") == "us-east-2"
    assert policy_details.get("PolicyType") == None
    assert policy_details.get("Policy") == None