# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckServerlessAppRepoForOrganizationsDependency
from resource_based_policy.resource_based_policy_model import PolicyAnalyzerResponse

logger = Logger(level="info")

principal_org_id_policy = {'ResourceName': 'test-application-1',
                           'Policy': '[{\"Actions\": [\"GetApplication\", \"ListApplicationVersions\", \"ListApplicationDependencies\",\"SearchApplications\", \"UnshareApplication\"], \"PrincipalOrgIDs\": [\"o-a1b1c3d4e5\"], \"Principals\": [\"*\"], \"StatementId\": \"b90708e4-8b1d-4147-ad13-63929c3432f3\"}]'
                           }
only_accounts_policy = {'ResourceName': 'test-application-2-no-org-dependency',
                            'Policy': '[{\"Actions\": [\"Deploy\"], \"PrincipalOrgIDs\": [], \"Principals\": [\"111111111111\", \"222222222222\"], \"StatementId\": \"0ee0378c-e658-4173-bfd4-e8ccd83cb17f\"}]'
                            }
accounts_and_org_id_policy = {'ResourceName': 'test-application-3-individual-accounts-in-organization',
                        'Policy': '[{\"Actions\": [\"Deploy\"], \"PrincipalOrgIDs\": [\"o-a1b1c3d4e5\"], \"Principals\": [\"333333333333\"], \"StatementId\": \"5e7609f1-8d53-44df-b990-238103cf6efc\"}]'
                        }
multiple_policies = {'ResourceName': 'test-app-multiple-statements-1',
                     'Policy': '[{\"Actions\": [\"Deploy\"], \"PrincipalOrgIDs\": [], \"Principals\": [\"222222222222\"], \"StatementId\": \"75138ec4-aabe-480e-ba66-993b26cd7d22\"}, {\"Actions\": [\"Deploy\", \"UnshareApplication\"], \"PrincipalOrgIDs\": [\"o-a1b1c3d4e5\"], \"Principals\": [\"*\"], \"StatementId\": \"7ea15ad8-59f9-4924-a8c9-b7f0fedf04d0\"}, {\"Actions\": [\"Deploy\"], \"PrincipalOrgIDs\": [\"o-a1b1c3d4e5\"], \"Principals\": [\"333333333333\", \"111111111111\"], \"StatementId\": \"04d95659-3818-4944-a428-8f4cdc18f688\"}]'
                     }


def test_check_policy_for_principal_org_id():

    # ACT
    response: list[PolicyAnalyzerResponse] = CheckServerlessAppRepoForOrganizationsDependency().scan([principal_org_id_policy])
    print(response)

    # ASSERT
    assert len(response) == 1
    for resource in response:
        assert resource['GlobalContextKey'] == 'aws:PrincipalOrgID'
        assert resource['OrganizationsResource'] == "o-a1b1c3d4e5"


def test_check_policy_for_only_accounts_no_org_dependency():
    # ACT
    response: list[PolicyAnalyzerResponse] = CheckServerlessAppRepoForOrganizationsDependency().scan([only_accounts_policy])
    print(response)

    # ASSERT
    assert response == []


def test_check_policy_for_accounts_and_org_dependency():
    # ACT
    response: list[PolicyAnalyzerResponse] = CheckServerlessAppRepoForOrganizationsDependency().scan(
        [accounts_and_org_id_policy])
    print(response)

    # ASSERT
    assert len(response) == 1
    for resource in response:
        assert resource['GlobalContextKey'] == 'aws:PrincipalOrgID'
        assert resource['OrganizationsResource'] == "o-a1b1c3d4e5"


def test_check_multiple_policies_with_and_without_org_dependency():
    # ACT
    response: list[PolicyAnalyzerResponse] = CheckServerlessAppRepoForOrganizationsDependency().scan(
        [multiple_policies])
    print(response)

    # ASSERT
    assert len(response) == 1
    for resource in response:
        assert resource['GlobalContextKey'] == 'aws:PrincipalOrgID'
        assert resource['OrganizationsResource'] == "o-a1b1c3d4e5"
