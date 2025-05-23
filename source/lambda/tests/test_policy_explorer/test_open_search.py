#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_opensearch.type_defs import DomainInfoTypeDef, DomainStatusTypeDef

from policy_explorer.policy_explorer_model import PolicyType
from policy_explorer.step_functions_lambda.scan_open_search_domain_policy import OpenSearchDomainPolicy
from tests.test_policy_explorer.mock_data import event

logger = Logger(level='info', service="test_code_build")


@mock_aws
def test_mock_opensearch_scan_policy_no_policies(mocker):
    # ARRANGE
    mock_opensearch(mocker)

    # ARRANGE
    response = OpenSearchDomainPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_aws
def test_mock_opensearch_scan_policy(mocker):
    # ARRANGE
    list_domain_names_response: list[DomainInfoTypeDef] = [
        {
            "DomainName": "mock_domain_name_1",
            "EngineType": "OpenSearch"
        },
        {
            "DomainName": "mock_domain_name_2",
            "EngineType": "OpenSearch"
        },
        {
            "DomainName": "mock_domain_name_3",
            "EngineType": "OpenSearch"
        },
        {
            "DomainName": "mock_domain_name_4",
            "EngineType": "OpenSearch"
        },
        {
            "DomainName": "mock_domain_name_5",
            "EngineType": "OpenSearch"
        },
        {
            "DomainName": "mock_domain_name_6",
            "EngineType": "OpenSearch"
        }
    ]

    describe_domains_response: list[DomainStatusTypeDef] = [
        {
            "DomainId": "mock_domain_id_1",
            "DomainName": "mock_domain_name_1",
            "ARN": "arn:aws:es:us-west-2:111111111111:domain/:mock_domain_name",
            "ClusterConfig": {
                "InstanceType": "c4.2xlarge.search",
                "InstanceCount": 1,
                "DedicatedMasterEnabled": False,
                "ZoneAwarenessEnabled": False,
                "ZoneAwarenessConfig": {
                    "AvailabilityZoneCount": 1,
                },
                "DedicatedMasterType": "c4.2xlarge.search",
                "DedicatedMasterCount": 1,
                "WarmEnabled": False,
                "WarmType": "ultrawarm1.large.search",
                "WarmCount": 1,
                "ColdStorageOptions": {
                    "Enabled": False,
                }
            },
            "AccessPolicies": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{"
                              "\"AWS\":\"*\"},\"Action\":\"es:ESHttp*\","
                              "\"Resource\":\"arn:aws:es:us-east-1:999999999999:domain/test-domain-1/*\","
                              "\"Condition\":{\"StringEquals\":{\"aws:RequestedRegion\":[\"eu-west-1\",\"eu-west-2\","
                              "\"eu-west-3\"]}}},{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"*\"},"
                              "\"Action\":\"es:ESHttp*\","
                              "\"Resource\":\"arn:aws:es:us-east-1:999999999999:domain/test-domain-1/*\","
                              "\"Condition\":{\"StringEquals\":{\"aws:PrincipalOrgID\":\"o-abcd1234\"}}}]}"
        },
        {
            "DomainId": "mock_domain_id_2",
            "DomainName": "mock_domain_name_2",
            "ARN": "arn:aws:es:us-west-2:111111111111:domain/:mock_domain_name_2",
            "ClusterConfig": {
                "InstanceType": "c4.2xlarge.search",
                "InstanceCount": 1,
                "DedicatedMasterEnabled": False,
                "ZoneAwarenessEnabled": False,
                "ZoneAwarenessConfig": {
                    "AvailabilityZoneCount": 1,
                },
                "DedicatedMasterType": "c4.2xlarge.search",
                "DedicatedMasterCount": 1,
                "WarmEnabled": False,
                "WarmType": "ultrawarm1.large.search",
                "WarmCount": 1,
                "ColdStorageOptions": {
                    "Enabled": False,
                }
            }
        },
        {
            "DomainId": "mock_domain_id_3",
            "DomainName": "mock_domain_name_3",
            "ARN": "arn:aws:es:us-west-2:111111111111:domain/:mock_domain_name_3",
            "ClusterConfig": {
                "InstanceType": "c4.2xlarge.search",
                "InstanceCount": 1,
                "DedicatedMasterEnabled": False,
                "ZoneAwarenessEnabled": False,
                "ZoneAwarenessConfig": {
                    "AvailabilityZoneCount": 1,
                },
                "DedicatedMasterType": "c4.2xlarge.search",
                "DedicatedMasterCount": 1,
                "WarmEnabled": False,
                "WarmType": "ultrawarm1.large.search",
                "WarmCount": 1,
                "ColdStorageOptions": {
                    "Enabled": False,
                }
            }
        },
        {
            "DomainId": "mock_domain_id_4",
            "DomainName": "mock_domain_name_4",
            "ARN": "arn:aws:es:us-west-2:111111111111:domain/:mock_domain_name_4",
            "ClusterConfig": {
                "InstanceType": "c4.2xlarge.search",
                "InstanceCount": 1,
                "DedicatedMasterEnabled": False,
                "ZoneAwarenessEnabled": False,
                "ZoneAwarenessConfig": {
                    "AvailabilityZoneCount": 1,
                },
                "DedicatedMasterType": "c4.2xlarge.search",
                "DedicatedMasterCount": 1,
                "WarmEnabled": False,
                "WarmType": "ultrawarm1.large.search",
                "WarmCount": 1,
                "ColdStorageOptions": {
                    "Enabled": False,
                }
            }
        },
        {
            "DomainId": "mock_domain_id_5",
            "DomainName": "mock_domain_name_5",
            "ARN": "arn:aws:es:us-west-2:111111111111:domain/:mock_domain_name_5",
            "ClusterConfig": {
                "InstanceType": "c4.2xlarge.search",
                "InstanceCount": 1,
                "DedicatedMasterEnabled": False,
                "ZoneAwarenessEnabled": False,
                "ZoneAwarenessConfig": {
                    "AvailabilityZoneCount": 1,
                },
                "DedicatedMasterType": "c4.2xlarge.search",
                "DedicatedMasterCount": 1,
                "WarmEnabled": False,
                "WarmType": "ultrawarm1.large.search",
                "WarmCount": 1,
                "ColdStorageOptions": {
                    "Enabled": False,
                }
            }
        },
        {
            "DomainId": "mock_domain_id_6",
            "DomainName": "mock_domain_name_6",
            "ARN": "arn:aws:es:us-west-2:111111111111:domain/:mock_domain_name_6",
            "ClusterConfig": {
                "InstanceType": "c4.2xlarge.search",
                "InstanceCount": 1,
                "DedicatedMasterEnabled": False,
                "ZoneAwarenessEnabled": False,
                "ZoneAwarenessConfig": {
                    "AvailabilityZoneCount": 1,
                },
                "DedicatedMasterType": "c4.2xlarge.search",
                "DedicatedMasterCount": 1,
                "WarmEnabled": False,
                "WarmType": "ultrawarm1.large.search",
                "WarmCount": 1,
                "ColdStorageOptions": {
                    "Enabled": False,
                }
            },
            "AccessPolicies": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{"
                              "\"AWS\":\"*\"},\"Action\":\"es:ESHttp*\","
                              "\"Resource\":\"arn:aws:es:us-east-1:999999999999:domain/test-domain-1/*\","
                              "\"Condition\":{\"StringEquals\":{\"aws:RequestedRegion\":[\"eu-west-1\",\"eu-west-2\","
                              "\"eu-west-3\"]}}},{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"*\"},"
                              "\"Action\":\"es:ESHttp*\","
                              "\"Resource\":\"arn:aws:es:us-east-1:999999999999:domain/test-domain-1/*\","
                              "\"Condition\":{\"StringEquals\":{\"aws:PrincipalOrgID\":\"o-abcd1234\"}}}]}"
        }
    ]

    mock_opensearch(mocker,
                    list_domain_names_response,
                    describe_domains_response)

    # ACT
    response = OpenSearchDomainPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 16
    for resource in response:
        assert resource.get('PartitionKey') == PolicyType.RESOURCE_BASED_POLICY.value


def mock_opensearch(mocker,
                    list_domain_names_response=None,
                    describe_domains_response=None):

    # ARRANGE
    if list_domain_names_response is None:
        list_domain_names_response = []

    if describe_domains_response is None:
        describe_domains_response = []

    def mock_list_domain_names(self):
        return list_domain_names_response

    mocker.patch(
        "aws.services.open_search.OpenSearch.list_domain_names",
        mock_list_domain_names
    )

    def mock_describe_domains(self, domain_names: list[str]):
        return describe_domains_response

    mocker.patch(
        "aws.services.open_search.OpenSearch.describe_domains",
        mock_describe_domains
    )
