# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from metrics.solution_metrics import SolutionMetrics
from tests.test_utils.testdata_factory import delegated_admin_create_request, trusted_access_create_request, \
    resource_based_policies_create_request


def test_returns_empty_list():
    # ARRANGE
    findings = []

    # ACT
    metrics = SolutionMetrics()._generate_metrics('DELEGATED_ADMIN', findings)

    # ASSERT
    assert metrics == {'AccountsCount': '0',
                       'AssessmentType': 'DELEGATED_ADMIN',
                       'FindingsCount': '0',
                       'RegionsCount': '0',
                       'ServicesCount': '0'}


def test_counts_delegated_admin_findings():
    # ARRANGE
    findings = [
        delegated_admin_create_request('s3.amazonaws.com', '111111111111'),
        delegated_admin_create_request('glacier.amazonaws.com', '111111111111'),
        delegated_admin_create_request('sns.amazonaws.com', '111111111111'),
        delegated_admin_create_request('sns.amazonaws.com', '222222222222'),
    ]

    # ACT
    metrics = SolutionMetrics()._generate_metrics('DELEGATED_ADMIN', findings)

    # ASSERT
    assert metrics == {'AssessmentType': 'DELEGATED_ADMIN',
                       'AccountsCount': '2',
                       'FindingsCount': '4',
                       'RegionsCount': '0',
                       'ServicesCount': '3'}


def test_counts_trusted_access_findings():
    # ARRANGE
    findings = [
        trusted_access_create_request('s3.amazonaws.com'),
        trusted_access_create_request('glacier.amazonaws.com'),
        trusted_access_create_request('sns.amazonaws.com'),
        trusted_access_create_request('sns.amazonaws.com'),
    ]

    # ACT
    metrics = SolutionMetrics()._generate_metrics('TRUSTED_ACCESS', findings)

    # ASSERT
    assert metrics == {'AssessmentType': 'TRUSTED_ACCESS',
                       'AccountsCount': '0',
                       'FindingsCount': '4',
                       'RegionsCount': '0',
                       'ServicesCount': '3'}


def test_counts_resource_based_policies_findings():
    # ARRANGE
    findings = [
        resource_based_policies_create_request('s3.amazonaws.com', 'us-east-1'),
        resource_based_policies_create_request('glacier.amazonaws.com', 'us-east-1'),
        resource_based_policies_create_request('sns.amazonaws.com', 'us-east-2'),
        resource_based_policies_create_request('sns.amazonaws.com', 'us-east-2'),
    ]

    # ACT
    metrics = SolutionMetrics()._generate_metrics('RESOURCE_BASED_POLICIES', findings)

    # ASSERT
    assert metrics == {'AssessmentType': 'RESOURCE_BASED_POLICIES',
                       'AccountsCount': '1',
                       'FindingsCount': '4',
                       'RegionsCount': '2',
                       'ServicesCount': '3'}
    
def test_if_version_is_included_in_the_metrics():
    # ARRANGE
    findings = [
        resource_based_policies_create_request('s3.amazonaws.com', 'us-east-1'),
        resource_based_policies_create_request('glacier.amazonaws.com', 'us-east-1'),
        resource_based_policies_create_request('sns.amazonaws.com', 'us-east-2'),
        resource_based_policies_create_request('sns.amazonaws.com', 'us-east-2'),
    ]

    # ACT
    metrics = SolutionMetrics()._generate_metrics('RESOURCE_BASED_POLICIES', findings)

    model = SolutionMetrics()._denormalize_to_metrics_model(metrics)
    assert model.get("Version") == "v1.0.0"
