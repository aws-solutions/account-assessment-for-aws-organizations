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
        assert 'Pagination' in body
        assert body['Pagination']['hasMoreResults'] == False

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

    def test_that_it_supports_pagination_with_max_results(policy_explorer_table):
        repository = PoliciesRepository()
        rbp1 = policy_create_request('ResourceBasedPolicy')
        rbp2 = policy_create_request('ResourceBasedPolicy')
        rbp3 = policy_create_request('ResourceBasedPolicy')

        created_rbps = repository.create_all([rbp1, rbp2, rbp3])

        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
                'maxResults': '2',
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        body = json.loads(result['body'])
        assert len(body['Results']) == 2
        assert 'Pagination' in body
        assert body['Pagination']['hasMoreResults'] in [True, False]

    def test_that_it_handles_default_max_results(policy_explorer_table):
        repository = PoliciesRepository()
        rbps = [policy_create_request('ResourceBasedPolicy') for _ in range(5)]
        created_rbps = repository.create_all(rbps)

        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        body = json.loads(result['body'])
        assert len(body['Results']) == 5
        assert 'Pagination' in body
        assert body['Pagination']['hasMoreResults'] == False

    def test_pagination_parameter_priority_max_results_over_limit(policy_explorer_table):
        repository = PoliciesRepository()
        rbps = [policy_create_request('ResourceBasedPolicy') for _ in range(5)]
        repository.create_all(rbps)

        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
                'limit': '3',
                'maxResults': '2',  # This should take priority
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        body = json.loads(result['body'])
        assert len(body['Results']) == 2  # Should use maxResults, not limit
        assert 'Pagination' in body

    def test_pagination_with_string_vs_integer_parameters(policy_explorer_table):
        # ARRANGE
        repository = PoliciesRepository()
        rbps = [policy_create_request('ResourceBasedPolicy') for _ in range(5)]
        repository.create_all(rbps)

        result1 = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
                'limit': 2,  # Integer
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        result2 = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
                'maxResults': '2',  # String
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        body1 = json.loads(result1['body'])
        body2 = json.loads(result2['body'])
        assert len(body1['Results']) == 2
        assert len(body2['Results']) == 2
        assert 'Pagination' in body1
        assert 'Pagination' in body2

    def test_pagination_boundary_conditions(policy_explorer_table):
        repository = PoliciesRepository()
        rbps = [policy_create_request('ResourceBasedPolicy') for _ in range(5)]
        repository.create_all(rbps)

        result1 = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
                'maxResults': '0',
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        result2 = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
                'maxResults': '2000',
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        result3 = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
                'maxResults': 'invalid',
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        body1 = json.loads(result1['body'])
        body2 = json.loads(result2['body'])
        body3 = json.loads(result3['body'])

        assert len(body1['Results']) == 5
        assert len(body2['Results']) == 5
        assert len(body3['Results']) == 5

    def test_invalid_next_token_handling(policy_explorer_table):
        repository = PoliciesRepository()
        rbps = [policy_create_request('ResourceBasedPolicy') for _ in range(3)]
        repository.create_all(rbps)

        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
                'maxResults': '2',
                'nextToken': 'invalid-token',
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'Results' in body
        assert 'Pagination' in body

    def test_pagination_response_structure(policy_explorer_table):
        repository = PoliciesRepository()
        rbps = [policy_create_request('ResourceBasedPolicy') for _ in range(3)]
        repository.create_all(rbps)

        # ACT
        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'GLOBAL',
                'maxResults': '2',
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        body = json.loads(result['body'])

        assert 'Results' in body
        assert isinstance(body['Results'], list)
        assert len(body['Results']) == 2

        assert 'Pagination' in body
        assert isinstance(body['Pagination'], dict)
        assert 'hasMoreResults' in body['Pagination']
        assert isinstance(body['Pagination']['hasMoreResults'], bool)

        if 'nextToken' in body['Pagination']:
            assert isinstance(body['Pagination']['nextToken'], (str, type(None)))
