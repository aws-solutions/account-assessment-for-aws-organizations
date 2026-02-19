#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json

from policy_explorer import read_policies
from policy_explorer.policy_explorer_repository import PoliciesRepository
from tests.test_utils.testdata_factory import policy_create_request, TestLambdaContext


def _fetch_all_pages(policy_type: str, region: str, filters: dict, page_size: int) -> list:
    """Fetch all pages of results, returning combined items."""
    query_params = {'region': region, 'maxResults': str(page_size)}
    query_params.update(filters)

    all_results = []
    pages = 0

    while True:
        result = read_policies.lambda_handler({
            "path": f"/policy-explorer/{policy_type}",
            'pathParameters': {'partitionKey': policy_type},
            'queryStringParameters': query_params,
            "httpMethod": "GET"
        }, TestLambdaContext())

        body = json.loads(result['body'])
        all_results.extend(body['Results'])
        pagination = body['Pagination']
        pages += 1

        if not pagination.get('nextToken') or not pagination.get('hasMoreResults'):
            break
        query_params['nextToken'] = pagination['nextToken']

        if pages > 50:
            raise Exception("Too many pages - possible infinite loop")

    return all_results


def _seed(repository, policy_type, count, region='GLOBAL', **overrides):
    """Create count items via repository."""
    items = [
        policy_create_request(policy_type, region=region, service=f'{overrides.get("service_prefix", "item")}-{i:04d}', **{k: v for k, v in overrides.items() if k != 'service_prefix'})
        for i in range(count)
    ]
    repository.create_all(items)
    return items


class TestSparseFilterMatches:
    """Core bug: sparse matches must all be found across pagination."""

    def test_finds_all_matches_at_1pct_rate(self, policy_explorer_table):
        repo = PoliciesRepository()
        target = "o-customerorg123"

        _seed(repo, 'ResourceBasedPolicy', 200, region='us-east-1',
              principal='{"AWS": "arn:aws:iam::111111111111:root"}', service_prefix='nomatch')
        _seed(repo, 'ResourceBasedPolicy', 10, region='us-east-1',
              principal=f'{{"AWS": "arn:aws:iam::{target}:root"}}', service_prefix='match')

        results = _fetch_all_pages('ResourceBasedPolicy', 'us-east-1', {'principal': target}, page_size=50)

        assert len(results) == 10
        assert all(target in r['Principal'] for r in results)

    def test_finds_all_matches_at_very_sparse_rate(self, policy_explorer_table):
        repo = PoliciesRepository()
        rare_action = "secretsmanager:GetSecretValue"

        _seed(repo, 'IdentityBasedPolicy', 300, action='["s3:GetObject"]', service_prefix='common')
        _seed(repo, 'IdentityBasedPolicy', 3, action=f'["{rare_action}"]', service_prefix='rare')

        results = _fetch_all_pages('IdentityBasedPolicy', 'GLOBAL', {'action': rare_action}, page_size=50)

        assert len(results) == 3
        assert all(rare_action in r['Action'] for r in results)


class TestPaginationTokenCorrectness:
    """Pagination tokens must not cause duplicates or skips."""

    def test_no_duplicates_across_pages(self, policy_explorer_table):
        repo = PoliciesRepository()
        _seed(repo, 'ServiceControlPolicy', 150, effect='Deny', service_prefix='scp')

        results = _fetch_all_pages('ServiceControlPolicy', 'GLOBAL', {'effect': 'Deny'}, page_size=30)

        sort_keys = [r['SortKey'] for r in results]
        assert len(sort_keys) == len(set(sort_keys)), "Duplicate items found"
        assert len(results) == 150

    def test_no_items_skipped(self, policy_explorer_table):
        repo = PoliciesRepository()
        target_org = "o-targetorg456"

        _seed(repo, 'ResourceBasedPolicy', 100, region='eu-west-1',
              condition='{"StringEquals": {"aws:PrincipalOrgID": "o-other"}}', service_prefix='other')
        _seed(repo, 'ResourceBasedPolicy', 60, region='eu-west-1',
              condition=f'{{"StringEquals": {{"aws:PrincipalOrgID": "{target_org}"}}}}', service_prefix='target')

        results = _fetch_all_pages('ResourceBasedPolicy', 'eu-west-1', {'condition': target_org}, page_size=15)

        assert len(results) == 60
        assert all(target_org in r['Condition'] for r in results)


class TestBoundaryConditions:

    def test_all_items_match(self, policy_explorer_table):
        repo = PoliciesRepository()
        _seed(repo, 'IdentityBasedPolicy', 80, effect='Allow', service_prefix='allow')

        results = _fetch_all_pages('IdentityBasedPolicy', 'GLOBAL', {'effect': 'Allow'}, page_size=30)
        assert len(results) == 80

    def test_no_items_match(self, policy_explorer_table):
        repo = PoliciesRepository()
        _seed(repo, 'ResourceBasedPolicy', 50, region='us-west-2',
              principal='{"AWS": "arn:aws:iam::111111111111:root"}', service_prefix='existing')

        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'us-west-2',
                'principal': 'nonexistent-xyz',
                'maxResults': '100'
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        body = json.loads(result['body'])
        assert len(body['Results']) == 0
        assert body['Pagination']['hasMoreResults'] is False

    def test_exact_page_size_matches(self, policy_explorer_table):
        repo = PoliciesRepository()
        bucket = "arn:aws:s3:::exact-match-bucket"
        _seed(repo, 'ResourceBasedPolicy', 50, region='ap-southeast-1',
              resource=f'"{bucket}"', service_prefix='exact')

        result = read_policies.lambda_handler({
            "path": "/policy-explorer/ResourceBasedPolicy",
            'pathParameters': {'partitionKey': 'ResourceBasedPolicy'},
            'queryStringParameters': {
                'region': 'ap-southeast-1',
                'resource': bucket,
                'maxResults': '50'
            },
            "httpMethod": "GET"
        }, TestLambdaContext())

        body = json.loads(result['body'])
        assert len(body['Results']) == 50


class TestMultipleFilters:

    def test_combined_filters_sparse_matches(self, policy_explorer_table):
        repo = PoliciesRepository()
        target_action = "iam:DeleteRole"

        _seed(repo, 'IdentityBasedPolicy', 100, effect='Allow',
              action='["s3:GetObject"]', service_prefix='allow-s3')
        _seed(repo, 'IdentityBasedPolicy', 100, effect='Deny',
              action='["s3:DeleteBucket"]', service_prefix='deny-s3')
        _seed(repo, 'IdentityBasedPolicy', 20, effect='Deny',
              action=f'["{target_action}"]', service_prefix='deny-iam')

        results = _fetch_all_pages('IdentityBasedPolicy', 'GLOBAL',
                                   {'effect': 'Deny', 'action': target_action}, page_size=10)

        assert len(results) == 20
        assert all(r['Effect'] == 'Deny' and target_action in r['Action'] for r in results)
