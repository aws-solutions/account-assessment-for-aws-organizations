# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from moto.core import DEFAULT_ACCOUNT_ID as ACCOUNT_ID

from resource_based_policy.resource_based_policy_model import ScanServiceRequestModel

mock_policies = [
    {
        "MockResourceName": "resource_1",
        "MockPolicyName": "principal-org-id-policy",
        "MockPolicy": {
            "Version": "2012-10-17",
            "Statement": {
                "Sid": "AllowPutObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:PutObject",
                "Resource": "arn:aws:s3:::policy-ninja-dev/*",
                "Condition": {"StringEquals": {"aws:PrincipalOrgID": "o-a1b2c3d4e5"}
                              }
            }
        }},

    {
        "MockResourceName": "resource_2",
        "MockPolicyName": "PrincipalOrgPathsPolicy",
        "MockPolicy": {
            "Version": "2012-10-17",
            "Statement": {
                "Sid": "AllowPutObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:PutObject",
                "Resource": "arn:aws:s3:::policy-ninja-dev/*",
                "Condition": {"ForAnyValue:StringEquals": {
                    "aws:PrincipalOrgPaths": ["o-a1b2c3d4e5/r-ab12/ou-ab12-11111111/ou-ab12-22222222/"]
                }}
            }
        }},

    {
        "MockResourceName": "resource_3",
        "MockPolicyName": "ResourceOrgIdPolicy",
        "MockPolicy": {
            "Version": "2012-10-17",
            "Statement": {
                "Sid": "DenyPutObjectToS3ResourcesOutsideMyOrganization",
                "Effect": "Deny",
                "Action": "s3:PutObject",
                "Resource": "arn:aws:s3:::policy-genius-dev/*",
                "Condition": {
                    "StringNotEquals": {
                        "aws:ResourceOrgID": "${aws:PrincipalOrgID}"
                    }
                }
            }
        }},

    {
        "MockResourceName": "resource_4", "MockPolicyName": "ResourceOrgPathsPolicy",
        "MockPolicy": {
            "Version": "2012-10-17",
            "Statement": {
                "Sid": "DenyPutObjectToS3ResourcesOutsideMyOrganization",
                "Effect": "Deny",
                "Action": "s3:PutObject",
                "Resource": "arn:aws:s3:::policy-genius-dev/*",
                "Condition": {"ForAnyValue:StringLike": {
                    "aws:ResourceOrgPaths": ["o-a1b2c3d4e5/r-ab12/ou-ab12-11111111/*"]
                }}
            }
        }},
    {
        "MockResourceName": "resource_5",
        "MockPolicyName": "PolicyWithWithMultipleKeys",
        "MockPolicy": {
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
        }},

    {
        "MockResourceName": "resource_6",
        "MockPolicyName": "PolicyWithWithMultipleStatementsAndKeys",
        "MockPolicy": {
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
    },
    {
        "MockResourceName": "resource_7",
        "MockPolicyName": "PolicyWithMultipleStatementsWithDependency",
        "MockPolicy": {
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
    },
    {
        "MockResourceName": "resource_8",
        "MockPolicyName": "PolicyWithMultipleStatementsOneWithDependencyOtherNot",
        "MockPolicy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "__owner_statement",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "arn:aws:iam::999999999999:root"
                    },
                    "Action": "SQS:*",
                    "Resource": "arn:aws:sqs:us-east-1:999999999999:test-queue-for-org"
                },
                {
                    "Sid": "test_queue_allow_orr",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "sqs:TagQueue",
                    "Resource": "arn:aws:sqs:us-east-1:999999999999:test-queue-for-org",
                    "Condition": {
                        "ArnEquals": {
                            "aws:PrincipalOrgID": "o-abcd1234"
                        }
                    }
                }
            ]
        }
    },
    {
        "MockResourceName": "ResourceWithNoPolicy",
    },
    {
        "MockPolicyName": "S3MockPolicy",
        "MockPolicy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "DenyAllAwsResourcesOutsideAccountExceptAmazonS3",
                    "Effect": "Deny",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:PutObjectAcl"
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringNotEquals": {
                            "aws:ResourceAccount": [
                                "111122223333"
                            ]
                        }
                    }
                },
                {
                    "Sid": "DenyAllS3ResourcesOutsideAccountExceptDataExchange",
                    "Effect": "Deny",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:PutObjectAcl"
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringNotEquals": {
                            "aws:ResourceAccount": [
                                "111122223333"
                            ]
                        },
                        "ForAllValues:StringNotEquals": {
                            "aws:CalledVia": [
                                "dataexchange.amazonaws.com"
                            ]
                        }
                    }
                }
            ]
        }},

    {
        "MockPolicyName": "DDBMockPolicy",
        "MockPolicy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "ListAndDescribe",
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:List*",
                        "dynamodb:DescribeReservedCapacity*",
                        "dynamodb:DescribeLimits",
                        "dynamodb:DescribeTimeToLive"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "SpecificTable",
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:BatchGet*",
                        "dynamodb:DescribeStream",
                        "dynamodb:DescribeTable",
                        "dynamodb:Get*",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                        "dynamodb:BatchWrite*",
                        "dynamodb:CreateTable",
                        "dynamodb:Delete*",
                        "dynamodb:Update*",
                        "dynamodb:PutItem"
                    ],
                    "Resource": "arn:aws:dynamodb:*:*:table/MyTable"
                }
            ]
        }}]

event: ScanServiceRequestModel = {
    "AccountId": ACCOUNT_ID,
    "JobId": "12345-45678-098765",
    "Regions": ["us-east-1", "eu-west-1"],
    "ServiceName": "mock"
}
