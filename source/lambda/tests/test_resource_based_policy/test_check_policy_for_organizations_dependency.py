# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json

from aws_lambda_powertools import Logger
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency
from resource_based_policy.resource_based_policy_model import PolicyDocumentModel, PolicyAnalyzerRequest, \
    PolicyAnalyzerResponse

logger = Logger(level="info")
principal_org_id_policy = {
    "Version": "2012-10-17",
    "Statement": {
        "Sid": "AllowPutObject",
        "Effect": "Allow",
        "Principal": "*",
        "Action": "s3:PutObject",
        "Resource": "arn:aws:s3:::policy-ninja-dev/*",
        "Condition": {"StringEquals":
                          {"aws:principalOrgID": "o-a1b2c3d4e5"}
                      }
    }
}

principal_org_paths_policy = {
    "Version": "2012-10-17",
    "Statement": {
        "Sid": "AllowPutObject",
        "Effect": "Allow",
        "Principal": "*",
        "Action": "s3:PutObject",
        "Resource": "arn:aws:s3:::policy-ninja-dev/*",
        "Condition": {"ForAnyValue:StringEquals": {
            "aws:principalOrgpaths": ["o-a1b2c3d4e5/r-ab12/ou-ab12-11111111/ou-ab12-22222222/"]
        }}
    }
}

resource_org_id_policy = {
    "Version": "2012-10-17",
    "Statement": {
        "Sid": "DenyPutObjectToS3ResourcesOutsideMyOrganization",
        "Effect": "Deny",
        "Action": "s3:PutObject",
        "Resource": "arn:partition:s3:::policy-genius-dev/*",
        "Condition": {
            "StringNotEquals": {
                "aws:ResourceorgID": "${aws:PrincipalOrgID}"
            }
        }
    }
}

resource_org_paths_policy = {
    "Version": "2012-10-17",
    "Statement": {
        "Sid": "DenyPutObjectToS3ResourcesOutsideMyOrganization",
        "Effect": "Deny",
        "Action": "s3:PutObject",
        "Resource": "arn:partition:s3:::policy-genius-dev/*",
        "Condition": {"ForAnyValue:StringLike": {
            "aws:ResourceOrgPaths": ["o-a1b2c3d4e5/r-ab12/ou-ab12-11111111/*"]
        }}
    }
}

policy_with_with_multiple_keys = {
    "Version": "2012-10-17",
    "Statement": {
        "Effect": "Allow",
        "Action": "ec2:CreateTags",
        "Resource": "arn:aws:ec2:::instance/*",
        "Condition": {
            "StringEquals": {
                "aws:RequestTag/environment": [
                    "preprod",
                    "production"
                ],
                "aws:RequestTag/team": [
                    "engineering"
                ]
            }
        }
    }
}

policy_with_with_multiple_statements_and_keys = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PrincipalPutObjectIfIpAddress",
            "Effect": "Allow",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::DOC-EXAMPLE-BUCKET3/*",
            "Condition": {
                "Bool": {"aws:ViaAWSService": "false"},
                "IpAddress": {"aws:SourceIp": "203.0.113.0"}
            }
        },
        {
            "Sid": "ServicePutObject",
            "Effect": "Allow",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::DOC-EXAMPLE-BUCKET/*",
            "Condition": {
                "Bool": {"aws:ViaAWSService": "true"}
            }
        }
    ]
}

policy_with_multiple_statements_with_dependency = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "__default_statement_ID",
            "Effect": "Allow",
            "Principal": {
                "AWS": "*"
            },
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
            "Principal": {
                "AWS": "*"
            },
            "Action": "sns:Publish",
            "Resource": "arn:aws:sns:us-east-1:999999999999:MyNotifications",
            "Condition": {
                "StringEquals": {
                    "aws:principalorgid": "o-a1b2c3d4e5"
                }
            }
        },
        {
                "Sid": "AllowPutObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:PutObject",
                "Resource": "arn:aws:s3:::policy-ninja-dev/*",
                "Condition": {"ForAnyValue:StringEquals": {
                    "aws:PrincipalOrgPaths": ["o-a1b2c3d4e5/r-ab12/ou-ab12-11111111/ou-ab12-22222222/"]
                    }
                }
            }
    ]
}

policy_with_with_multiple_keys_string: str = json.dumps(policy_with_with_multiple_keys)
policy_with_with_multiple_statements_and_keys_string = json.dumps(policy_with_with_multiple_statements_and_keys)
policies_with_no_org_dependencies = [
    {'ResourceName': "Resource-22222222",
     'Policy': policy_with_with_multiple_keys_string},
    {'ResourceName': "Resource-33333333",
     'Policy': policy_with_with_multiple_statements_and_keys_string}]


def test_check_policy_for_principal_org_id():
    # ARRANGE
    principal_org_id_policy_string: str = json.dumps(principal_org_id_policy)
    policies: list[PolicyAnalyzerRequest] = [
        {'ResourceName': "Resource-11111111",
         'Policy': principal_org_id_policy_string}
    ]
    policies.extend(policies_with_no_org_dependencies)

    # ACT
    response: list[PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(policies)
    logger.info(response)

    # ASSERT
    for resource in response:
        assert resource['GlobalContextKey'].lower() == 'aws:PrincipalOrgID'.lower()
        assert isinstance(resource['OrganizationsResource'], str)


def test_check_policy_for_principal_org_paths():
    # ARRANGE
    principal_org_paths_policy_string: str = json.dumps(principal_org_paths_policy)
    policies: list[PolicyAnalyzerRequest] = [
        {'ResourceName': "Resource-11111111",
         'Policy': principal_org_paths_policy_string}
    ]
    policies.extend(policies_with_no_org_dependencies)

    # ACT
    response: list[PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(policies)
    print(response)

    # ASSERT
    for resource in response:
        assert resource['GlobalContextKey'].lower() == 'aws:PrincipalOrgPaths'.lower()
        assert isinstance(resource['OrganizationsResource'], list)


def test_check_policy_for_resource_org_id():
    # ARRANGE
    resource_org_id_policy_string: str = json.dumps(resource_org_id_policy)
    policies: list[PolicyAnalyzerRequest] = [
        {'ResourceName': "Resource-11111111",
         'Policy': resource_org_id_policy_string}
    ]
    policies.extend(policies_with_no_org_dependencies)

    # ACT
    response: list[PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(policies)
    print(response)

    # ASSERT
    for resource in response:
        assert resource['GlobalContextKey'].lower() == 'aws:ResourceOrgID'.lower()
        assert isinstance(resource['OrganizationsResource'], str)


def test_check_policy_for_resource_org_paths():
    # ARRANGE
    resource_org_paths_policy_string: str = json.dumps(resource_org_paths_policy)
    policies: list[PolicyAnalyzerRequest] = [
        {'ResourceName': "Resource-11111111",
         'Policy': resource_org_paths_policy_string}
    ]
    policies.extend(policies_with_no_org_dependencies)

    # ACT
    response: list[PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(policies)
    print(response)

    # ASSERT
    for resource in response:
        assert resource['GlobalContextKey'].lower() == 'aws:ResourceOrgPaths'.lower()
        assert isinstance(resource['OrganizationsResource'], list)


def test_check_policy_no_match():
    # ARRANGE
    policies: list[PolicyAnalyzerRequest] = []
    policies.extend(policies_with_no_org_dependencies)

    # ACT
    response: list[PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(policies)
    print(response)

    # ASSERT
    assert response == []


def test_check_policy_multiple_statement_with_org_dependency():
    # ARRANGE
    policy_str = json.dumps(policy_with_multiple_statements_with_dependency)
    policies: list[PolicyAnalyzerRequest] = [
        {'ResourceName': "Resource-22222222",
         'Policy': policy_str}
    ]

    # ACT
    response: list[PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(policies)
    print(response)

    # ASSERT
    assert len(response) == 2

    assert response[0]['GlobalContextKey'].lower() == 'aws:PrincipalOrgID'.lower()
    assert isinstance(response[0]['OrganizationsResource'], str)
    assert response[0]['OrganizationsResource'] == "o-a1b2c3d4e5"

    assert response[1]['GlobalContextKey'].lower() == 'aws:PrincipalOrgPaths'.lower()
    assert isinstance(response[1]['OrganizationsResource'], list)
    assert response[1]['OrganizationsResource'] == ["o-a1b2c3d4e5/r-ab12/ou-ab12-11111111/ou-ab12-22222222/"]


def test_api_gateway_policy_with_multiple_backslashes():
    # ARRANGE
    policies: list[PolicyAnalyzerRequest] = [{'ResourceName': 'PetStore',
                                             'Policy': '{\\\\\"Version\\\\\":\\\\\"2012-10-17\\\\\",\\\\\"Statement\\\\\":[{\\\\\"Effect\\\\\":\\\\\"Allow\\\\\",\\\\\"Principal\\\\\":{\\\\\"AWS\\\\\":\\\\\"*\\\\\"},\\\\\"Action\\\\\":\\\\\"execute-api:Invoke\\\\\",\\\\\"Resource\\\\\":\\\\\"arn:aws:execute-api:sa-east-1:333333333333:kp4of8w5k1\\\\/{{stageNameOrWildcard*}}\\\\/{{httpVerbOrWildcard*}}\\\\/{{resourcePathOrWildcard*}}\\\\\",\\\\\"Condition\\\\\":{\\\\\"StringEquals\\\\\":{\\\\\"aws:PrincipalOrgID\\\\\":\\\\\"o-a1b2c3d4e5\\\\\"}}}]}'}
        ]
    # ACT
    response: list[PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(policies)
    print(response)

    # ASSERT
    assert len(response) == 1
    for resource in response:
        assert resource['GlobalContextKey'].lower() == 'aws:PrincipalOrgID'.lower()
        assert isinstance(resource['OrganizationsResource'], str)
