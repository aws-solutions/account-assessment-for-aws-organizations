#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

from mypy_boto3_dynamodb.service_resource import Table

from policy_explorer import read_policies
from policy_explorer.policy_explorer_repository import PoliciesRepository
from tests.test_utils.testdata_factory import policy_create_request, TestLambdaContext


def describe_read_policies():
    scp1 = policy_create_request('ServiceControlPolicy', 'organizations', 'dev-account-id')
    scp2 = policy_create_request('ServiceControlPolicy', 'kms', 'dev-1-account-id')
    scp3 = policy_create_request('ServiceControlPolicy', 'mediastore', 'dev-2-account-id')
    rbp1 = policy_create_request('ResourceBasedPolicy', 'organizations', 'dev-account-id')
    rbp2 = policy_create_request('ResourceBasedPolicy', 'kms', 'dev-1-account-id')
    rbp3 = policy_create_request('ResourceBasedPolicy', 'mediastore', 'dev-2-account-id')
    ibp1 = policy_create_request('IdentityBasedPolicy', 'iam', 'dev-account-id')
    ibp2 = policy_create_request('IdentityBasedPolicy', 'iam', 'dev-1-account-id')
    ibp3 = policy_create_request('IdentityBasedPolicy', 'iam', 'dev-2-account-id')

    def test_that_it_returns_an_empty_list(policy_explorer_table: Table):
        # ARRANGE

        # ACT
        result = read_policies.lambda_handler({
            "path": "/policy-explorer/IdentityBasedPolicy",
            'pathParameters': {'partitionKey': 'IdentityBasedPolicy'},
            'queryStringParameters': {'region': 'GLOBAL'},
            "httpMethod": "GET"
        }, TestLambdaContext())

        # ASSERT
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['Results'] == []

    def test_that_it_returns_all_service_control_policies(policy_explorer_table):
        # ARRANGE
        repository = PoliciesRepository()
        created_scps = repository.create_all([scp1, scp2, scp3])
        repository.create_all([ibp1, ibp2, ibp3, rbp1, rbp2, rbp3])

        # ACT
        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ServiceControlPolicy",
            'pathParameters': {'partitionKey': 'ServiceControlPolicy'},
            'queryStringParameters': {'region': 'GLOBAL'},
            "httpMethod": "GET"
        }, TestLambdaContext())

        # ASSERT
        body = json.loads(result['body'])['Results']
        assert len(body) == 3
        assert created_scps[0] in body
        assert created_scps[1] in body
        assert created_scps[2] in body

    def test_that_it_returns_all_resource_based_policies(policy_explorer_table):
        # ARRANGE
        repository = PoliciesRepository()
        created_rbps = repository.create_all([rbp1, rbp2, rbp3])
        repository.create_all([ibp1, ibp2, ibp3, scp1, scp2, scp3])

        # ACT
        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {'region': 'GLOBAL'},
            "httpMethod": "GET"
        }, TestLambdaContext())

        # ASSERT
        body = json.loads(result['body'])['Results']
        assert len(body) == 3
        assert created_rbps[0] in body
        assert created_rbps[1] in body
        assert created_rbps[2] in body

    def test_that_it_returns_all_identity_based_policies(policy_explorer_table):
        # ARRANGE
        repository = PoliciesRepository()
        created_ibps = repository.create_all([ibp1, ibp2, ibp3])
        repository.create_all([rbp1, rbp2, rbp3, scp1, scp2, scp3])

        # ACT
        result = read_policies.lambda_handler({
            "path": "/policy-explorer/IdentityBasedPolicy",
            'pathParameters': {'partitionKey': 'IdentityBasedPolicy'},
            'queryStringParameters': {'region': 'GLOBAL'},
            "httpMethod": "GET"
        }, TestLambdaContext())

        # ASSERT
        body = json.loads(result['body'])['Results']
        assert len(body) == 3
        assert created_ibps[0] in body
        assert created_ibps[1] in body
        assert created_ibps[2] in body

    def test_that_it_filters_by_region(policy_explorer_table):
        # ARRANGE
        repository = PoliciesRepository()
        rbp1 = policy_create_request('ResourceBasedPolicy', region='us-east-1')
        rbp2 = policy_create_request('ResourceBasedPolicy', region='us-east-2')
        rbp3 = policy_create_request('ResourceBasedPolicy', region='GLOBAL')

        created_rbps = repository.create_all([rbp1, rbp2, rbp3])

        # ACT
        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {'region': 'us-east-1'},
            "httpMethod": "GET"
        }, TestLambdaContext())

        # ASSERT
        body = json.loads(result['body'])['Results']
        assert len(body) == 1
        assert created_rbps[0] in body
        assert created_rbps[1] not in body
        assert created_rbps[2] not in body

    def test_that_it_filters_by_principal_and_notprincipal(policy_explorer_table):
        # ARRANGE
        repository = PoliciesRepository()
        rbp1 = policy_create_request('ResourceBasedPolicy',
                                     principal='{"Service": "ssm.amazonaws.com"}',
                                     not_principal='{"AWS": "arn:aws:iam::123456789012:root"}')
        rbp2 = policy_create_request('ResourceBasedPolicy',
                                     principal='{"Service": "ssm.amazonaws.com"}',
                                     not_principal='{"Service": "apigateway.amazonaws.com"}')
        rbp3 = policy_create_request('ResourceBasedPolicy',
                                     principal='{"AWS": "arn:aws:iam::123456789012:root"}',
                                     not_principal='{"Service": "apigateway.amazonaws.com"}')

        created_rbps = repository.create_all([rbp1, rbp2, rbp3])

        # ACT
        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
                'principal': 'ssm.amazonaws.com',
                'notPrincipal': 'apigateway.amazonaws.com',
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        # ASSERT
        body = json.loads(result['body'])['Results']
        assert len(body) == 1
        assert created_rbps[0] not in body
        assert created_rbps[1] in body  # matches both principal and not_principal
        assert created_rbps[2] not in body

    def test_that_it_filters_by_action_and_notaction(policy_explorer_table):
        # ARRANGE
        repository = PoliciesRepository()
        rbp1 = policy_create_request('ResourceBasedPolicy',
                                     action='"sts:AssumeRole"',
                                     not_action='"kms:*"')
        rbp2 = policy_create_request('ResourceBasedPolicy',
                                     action='"sts:AssumeRole"',
                                     not_action='["mediastore:GetObject", "mediastore:DescribeObject"]')
        rbp3 = policy_create_request('ResourceBasedPolicy',
                                     action='["kms:Describe*", "kms:Get*", "kms:List*"]',
                                     not_action='["mediastore:GetObject", "mediastore:DescribeObject"]')

        created_rbps = repository.create_all([rbp1, rbp2, rbp3])

        # ACT
        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
                'action': '"sts:AssumeRole"',
                'notAction': '["mediastore:GetObject", "mediastore:DescribeObject"]',
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        # ASSERT
        body = json.loads(result['body'])['Results']
        assert len(body) == 1
        assert created_rbps[0] not in body
        assert created_rbps[1] in body  # matches both action and not_action
        assert created_rbps[2] not in body

    def test_that_it_filters_by_resource_and_notresource(policy_explorer_table):
        # ARRANGE
        repository = PoliciesRepository()
        rbp1 = policy_create_request('ResourceBasedPolicy',
                                     resource='"*"',
                                     not_resource='"arn:aws:ram:us-east-1:111122223333:resource-share-invitation/*"')
        rbp2 = policy_create_request('ResourceBasedPolicy',
                                     resource='"*"',
                                     not_resource='"arn:aws:events:us-east-1:111122223333:event-bus/STNO-EventBridge"')
        rbp3 = policy_create_request('ResourceBasedPolicy',
                                     resource='"arn:aws:ram:us-east-1:111122223333:resource-share-invitation/*"',
                                     not_resource='"arn:aws:events:us-east-1:111122223333:event-bus/STNO-EventBridge"')

        created_rbps = repository.create_all([rbp1, rbp2, rbp3])

        # ACT
        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
                'resource': '"*"',
                'notResource': '"arn:aws:events:us-east-1:111122223333:event-bus/STNO-EventBridge"',
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        # ASSERT
        body = json.loads(result['body'])['Results']
        assert len(body) == 1
        assert created_rbps[0] not in body
        assert created_rbps[1] in body  # matches both resource and not_resource
        assert created_rbps[2] not in body

    def test_that_it_filters_by_condition_and_effect(policy_explorer_table):
        # ARRANGE
        repository = PoliciesRepository()
        rbp1 = policy_create_request('ResourceBasedPolicy',
                                     condition='{"Bool": {"aws:SecureTransport": "true"}}',
                                     effect='Deny')
        rbp2 = policy_create_request('ResourceBasedPolicy',
                                     condition='{"Bool": {"aws:SecureTransport": "true"}}',
                                     effect='Allow')
        rbp3 = policy_create_request('ResourceBasedPolicy',
                                     condition='{"StringEquals": {"kms:ViaService": "lambda.us-east-1.amazonaws.com", "kms:CallerAccount": "111122223333"}}',
                                     effect='Allow')

        created_rbps = repository.create_all([rbp1, rbp2, rbp3])

        # ACT
        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
                'condition': 'SecureTransport',
                'effect': 'Allow',
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        # ASSERT
        body = json.loads(result['body'])['Results']
        assert len(body) == 1
        assert created_rbps[0] not in body
        assert created_rbps[1] in body  # matches both condition and effect
        assert created_rbps[2] not in body

    def test_that_it_limits_the_result_length(policy_explorer_table):
        # ARRANGE
        repository = PoliciesRepository()
        rbp1 = policy_create_request('ResourceBasedPolicy')
        rbp2 = policy_create_request('ResourceBasedPolicy')
        rbp3 = policy_create_request('ResourceBasedPolicy')

        created_rbps = repository.create_all([rbp1, rbp2, rbp3])

        # ACT
        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
                'limit': 2,
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        # ASSERT
        body = json.loads(result['body'])['Results']
        assert len(body) == 2
