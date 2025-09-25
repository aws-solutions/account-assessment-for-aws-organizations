#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json

from policy_explorer import read_policies
from policy_explorer.policy_explorer_repository import PoliciesRepository
from tests.test_utils.testdata_factory import policy_create_request, TestLambdaContext


def describe_policy_explorer_pagination_bug_fix():

    def test_search_results_beyond_first_page(policy_explorer_table):
        repository = PoliciesRepository()
        total_policies = 1000
        
        policies = []
        
        for i in range(int(total_policies * 0.9)):
            policies.append(policy_create_request(
                'ResourceBasedPolicy',
                principal='{"AWS": "arn:aws:iam::123456789012:root"}',
                region='us-east-1'
            ))
        
        search_principal = "special-search-principal.amazonaws.com"
        for i in range(int(total_policies * 0.1)):
            policies.append(policy_create_request(
                'ResourceBasedPolicy',
                principal=f'{{"Service": "{search_principal}"}}',
                region='us-east-1'
            ))
        
        repository.create_all(policies)
        
        page_size = 200
        
        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'us-east-1',
                'principal': search_principal,
                'maxResults': str(page_size)
            },
            "httpMethod": "GET"
        }, TestLambdaContext())
        
        body = json.loads(result['body'])
        results = body['Results']
        pagination = body['Pagination']
        
        all_found_policies = results.copy()
        
        while pagination.get('nextToken') and pagination.get('hasMoreResults'):
            next_result = read_policies.lambda_handler({
                "path": "/policy-explorer/ResourceBasedPolicy",
                'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
                'queryStringParameters': {
                    'region': 'us-east-1',
                    'principal': search_principal,
                    'maxResults': str(page_size),
                    'nextToken': pagination.get('nextToken')
                },
                "httpMethod": "GET"
            }, TestLambdaContext())
            
            next_body = json.loads(next_result['body'])
            all_found_policies.extend(next_body['Results'])
            pagination = next_body['Pagination']
        
        assert len(all_found_policies) == int(total_policies * 0.1)
        
        for policy in all_found_policies:
            assert search_principal in policy['Principal']

    def test_search_with_exact_boundary_pagination(policy_explorer_table):
        repository = PoliciesRepository()
        
        policies = []
        
        for i in range(100):
            policies.append(policy_create_request(
                'ResourceBasedPolicy',
                resource='"arn:aws:s3:::standard-bucket"',
                region='us-east-1'
            ))
        
        search_resource = "arn:aws:s3:::special-search-bucket"
        for i in range(20):
            policies.append(policy_create_request(
                'ResourceBasedPolicy',
                resource=f'"{search_resource}"',
                region='us-east-1'
            ))
        
        repository.create_all(policies)
        
        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'us-east-1',
                'resource': search_resource,
                'maxResults': '100'
            },
            "httpMethod": "GET"
        }, TestLambdaContext())
        
        body = json.loads(result['body'])
        first_page_results = body['Results']
        pagination = body['Pagination']
        
        second_page_results = []
        if pagination.get('nextToken') and pagination.get('hasMoreResults'):
            next_result = read_policies.lambda_handler({
                "path": "/policy-explorer/ResourceBasedPolicy",
                'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
                'queryStringParameters': {
                    'region': 'us-east-1',
                    'resource': search_resource,
                    'maxResults': '100',
                    'nextToken': pagination.get('nextToken')
                },
                "httpMethod": "GET"
            }, TestLambdaContext())
            
            next_body = json.loads(next_result['body'])
            second_page_results = next_body['Results']
        
        all_found_policies = first_page_results + second_page_results
        assert len(all_found_policies) == 20
        
        for policy in all_found_policies:
            assert search_resource in policy['Resource']
            
    def test_large_dataset_with_10000_policies(policy_explorer_table):
        repository = PoliciesRepository()
        total_policies = 10000
        
        policies = []
        
        for i in range(int(total_policies * 0.9)):
            policies.append(policy_create_request(
                'IdentityBasedPolicy',
                effect='Allow',
                region='us-east-1'
            ))
        
        search_effect = "Deny"
        for i in range(int(total_policies * 0.1)):
            policies.append(policy_create_request(
                'IdentityBasedPolicy',
                effect=search_effect,
                region='us-east-1'
            ))
        
        repository.create_all(policies)
        
        page_size = 500
        
        result = read_policies.lambda_handler({
            "path": "/policy-explorer/IdentityBasedPolicy",
            'pathParameters': {'partitionKey': 'IdentityBasedPolicy'},
            'queryStringParameters': {
                'region': 'us-east-1',
                'effect': search_effect,
                'maxResults': str(page_size)
            },
            "httpMethod": "GET"
        }, TestLambdaContext())
        
        body = json.loads(result['body'])
        results = body['Results']
        pagination = body['Pagination']
        
        all_found_policies = results.copy()
        
        page_count = 1
        while pagination.get('nextToken') and pagination.get('hasMoreResults'):
            page_count += 1
            next_result = read_policies.lambda_handler({
                "path": "/policy-explorer/IdentityBasedPolicy",
                'pathParameters': {'partitionKey': 'IdentityBasedPolicy'},
                'queryStringParameters': {
                    'region': 'us-east-1',
                    'effect': search_effect,
                    'maxResults': str(page_size),
                    'nextToken': pagination.get('nextToken')
                },
                "httpMethod": "GET"
            }, TestLambdaContext())
            
            next_body = json.loads(next_result['body'])
            all_found_policies.extend(next_body['Results'])
            pagination = next_body['Pagination']
        
        assert len(all_found_policies) == int(total_policies * 0.1)
        
        for policy in all_found_policies:
            assert policy['Effect'] == search_effect
            
        assert page_count > 1