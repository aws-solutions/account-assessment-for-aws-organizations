import boto3
from botocore.config import Config
from aws_lambda_powertools import Logger
import json
from typing import TypedDict, List
from enum import Enum
from policy_explorer.step_functions_lambda.convert_policy_into_dynamodb_items import ConvertPolicyIntoDynamoDBItems
from policy_explorer.policy_explorer_model import PolicyDetails, PolicyType


logger = Logger(level="debug")

    
def test_policy_parser_for_policy_with_single_statement():
    
    convert_policy_into_ddb_items = ConvertPolicyIntoDynamoDBItems()
    
    policy_type = PolicyType.RESOURCE_BASED_POLICY
    region = "us-east-2"
    account_id = "111122223333"
    service = "network-firewall"
    resource_identifier = "firewall-policy/Firewall-Policy-1-022237916e0b"
    policy = '{"Version":"2012-10-17","Statement":[{"Sid":"398671a9-cb7d-42b0-80fc-88d53be1681a-org-principals","Effect":"Allow","Principal":{"AWS":"arn:aws:iam::222233334444:root"},"Action":["network-firewall:AssociateFirewallPolicy","network-firewall:ListFirewallPolicies"],"Resource":"arn:aws:network-firewall:us-east-2:111122223333:firewall-policy/Firewall-Policy-1-022237916e0b","Condition":{"StringEquals":{"aws:PrincipalOrgID":"o-eci09zojnh"}}}]}'
    
    formatted_dynamodb_items = convert_policy_into_ddb_items.create_items(PolicyDetails(
        PolicyType=policy_type,
        Region=region,
        AccountId=account_id,
        Service=service,
        ResourceIdentifier=resource_identifier,
        Policy=policy
    ))
    
    assert len(formatted_dynamodb_items) == 1
    assert formatted_dynamodb_items[0]['PartitionKey'] == 'ResourceBasedPolicy'
    assert formatted_dynamodb_items[0]['SortKey'] == 'us-east-2#network-firewall#111122223333#firewall-policy/Firewall-Policy-1-022237916e0b#1'


def test_policy_parser_for_policy_with_multiple_statements():
    
    convert_policy_into_ddb_items = ConvertPolicyIntoDynamoDBItems()
    
    policy_type = PolicyType.RESOURCE_BASED_POLICY
    region = "us-east-2"
    account_id = "111122223333"
    service = "network-firewall"
    resource_identifier = "firewall-policy/Firewall-Policy-2-022237916e0b"
    policy = '{"Version":"2012-10-17","Statement":[{"Sid":"398671a9-cb7d-42b0-80fc-88d53be1681a-org-principals","Effect":"Allow","Principal":{"AWS":"arn:aws:iam::222233334444:root"},"Action":["network-firewall:AssociateFirewallPolicy","network-firewall:ListFirewallPolicies"],"Resource":"arn:aws:network-firewall:us-east-2:111122223333:firewall-policy/Firewall-Policy-1-022237916e0b","Condition":{"StringEquals":{"aws:PrincipalOrgID":"o-eci09zojnh"}}},{"Sid":"398671a9-cb7d-42b0-80fc-88d53be1681a-org-principals","Effect":"Allow","Principal":{"AWS":"arn:aws:iam::222233334444:root"},"Action":["network-firewall:AssociateFirewallPolicy","network-firewall:ListFirewallPolicies"],"Resource":"arn:aws:network-firewall:us-east-2:111122223333:firewall-policy/Firewall-Policy-1-022237916e0b","Condition":{"StringEquals":{"aws:PrincipalOrgID":"o-eci09zojnh"}}}]}'
    
    formatted_dynamodb_items = convert_policy_into_ddb_items.create_items(PolicyDetails(
        PolicyType=policy_type,
        Region=region,
        AccountId=account_id,
        Service=service,
        ResourceIdentifier=resource_identifier,
        Policy=policy
    ))
    
    assert len(formatted_dynamodb_items) == 2
    assert formatted_dynamodb_items[0]['SortKey'] == 'us-east-2#network-firewall#111122223333#firewall-policy/Firewall-Policy-2-022237916e0b#1'
    assert formatted_dynamodb_items[1]['SortKey'] == 'us-east-2#network-firewall#111122223333#firewall-policy/Firewall-Policy-2-022237916e0b#2'
    assert formatted_dynamodb_items[0]['Principal'] == '{"AWS": "arn:aws:iam::222233334444:root"}'
    assert formatted_dynamodb_items[1]['Condition'] == '{"StringEquals": {"aws:PrincipalOrgID": "o-eci09zojnh"}}'
    assert formatted_dynamodb_items[0]['PartitionKey'] == 'ResourceBasedPolicy'

def test_policy_parser_for_policy_with_escape_character():
    
    convert_policy_into_ddb_items = ConvertPolicyIntoDynamoDBItems()
    
    policy_type = PolicyType.RESOURCE_BASED_POLICY
    region = "us-east-2"
    account_id = "111111111111"
    service = "acm-pca"
    resource_identifier = "certificate-authority/942cc890-3671-485f-87e3-a52a39c77591"
    policy = '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"d5b46682-fe03-4ee3-af97-2cb7b5db2d23-org\",\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"acm-pca:IssueCertificate\",\"Resource\":\"arn:aws:acm-pca:us-east-2:111111111111:certificate-authority/942cc890-3671-485f-87e3-a52a39c77591\",\"Condition\":{\"StringEquals\":{\"aws:PrincipalOrgID\":\"o-eci09zojnh\",\"acm-pca:TemplateArn\":\"arn:aws:acm-pca:::template/EndEntityCertificate/V1\"},\"StringNotEquals\":{\"aws:PrincipalAccount\":\"111111111111\"}}},{\"Sid\":\"d5b46682-fe03-4ee3-af97-2cb7b5db2d23-org\",\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":[\"acm-pca:DescribeCertificateAuthority\",\"acm-pca:GetCertificate\",\"acm-pca:GetCertificateAuthorityCertificate\",\"acm-pca:ListPermissions\",\"acm-pca:ListTags\"],\"Resource\":\"arn:aws:acm-pca:us-east-2:111111111111:certificate-authority/942cc890-3671-485f-87e3-a52a39c77591\",\"Condition\":{\"StringEquals\":{\"aws:PrincipalOrgID\":\"o-eci09zojnh\"},\"StringNotEquals\":{\"aws:PrincipalAccount\":\"111111111111\"}}}]}'
    
    formatted_dynamodb_items = convert_policy_into_ddb_items.create_items(PolicyDetails(
        PolicyType=policy_type,
        Region=region,
        AccountId=account_id,
        Service=service,
        ResourceIdentifier=resource_identifier,
        Policy=policy
    ))
    
    assert len(formatted_dynamodb_items) == 2
    assert formatted_dynamodb_items[0]['SortKey'] == 'us-east-2#acm-pca#111111111111#certificate-authority/942cc890-3671-485f-87e3-a52a39c77591#1'
    assert formatted_dynamodb_items[0]['Principal'] == '"*"'
    assert formatted_dynamodb_items[0]['PartitionKey'] == 'ResourceBasedPolicy'

def test_policy_parser_for_policy_with_policy_as_dict():
    
    convert_policy_into_ddb_items = ConvertPolicyIntoDynamoDBItems()
    
    policy_type = PolicyType.RESOURCE_BASED_POLICY
    region = "us-east-2"
    account_id = "111111111111"
    service = "acm-pca"
    resource_identifier = "certificate-authority/942cc890-3671-485f-87e3-a52a39c77591"
    policy_string = '{ \
        "Version":"2012-10-17", \
        "Statement":[ \
                { \
                    "Sid":"d5b46682-fe03-4ee3-af97-2cb7b5db2d23-org", \
                    "Effect": "Allow", \
                    "Principal":"*", \
                    "Action":"acm-pca:IssueCertificate", \
                    "Resource": "*", \
                    "Condition": { \
                        "StringEquals": { \
                            "aws:PrincipalOrgID":"o-eci09zojnh", \
                            "acm-pca:TemplateArn":"arn:aws:acm-pca:::template/EndEntityCertificate/V1" \
                        } \
                    }  \
                } \
            ] \
        }'
    policy_dict = json.loads(policy_string)
    
    formatted_dynamodb_items = convert_policy_into_ddb_items.create_items(PolicyDetails(
        PolicyType=policy_type,
        Region=region,
        AccountId=account_id,
        Service=service,
        ResourceIdentifier=resource_identifier,
        Policy=policy_dict
    ))
    
    assert len(formatted_dynamodb_items) == 1
    assert formatted_dynamodb_items[0]['SortKey'] == 'us-east-2#acm-pca#111111111111#certificate-authority/942cc890-3671-485f-87e3-a52a39c77591#1'
    assert formatted_dynamodb_items[0]['Principal'] == '"*"'
    assert formatted_dynamodb_items[0]['PartitionKey'] == 'ResourceBasedPolicy'
    
    
def test_parameter_validation_for_create_items_for_dynamodb():
    
    convert_policy_into_ddb_items = ConvertPolicyIntoDynamoDBItems()
    
    formatted_dynamodb_items = convert_policy_into_ddb_items.create_items(PolicyDetails(
        PartitionKey=None,
        SortKey=None,
        Region=None,
        AccountId=None,
        Service=None,
        ResourceIdentifier=None,
        Policy=None))
    
    assert len(formatted_dynamodb_items) == 0


def test_create_sort_key():
    policy_type = PolicyType.RESOURCE_BASED_POLICY
    region = "us-east-2"
    account_id = "111111111111"
    service = "acm-pca"
    resource_identifier = "certificate-authority/942cc890-3671-485f-87e3-a52a39c77591"
    expected = "us-east-2#acm-pca#111111111111#certificate-authority/942cc890-3671-485f-87e3-a52a39c77591#1"
    convert_policy_into_ddb_items = ConvertPolicyIntoDynamoDBItems()
    response = convert_policy_into_ddb_items.create_sort_key(PolicyDetails(
        PolicyType=policy_type,
        Region=region,
        AccountId=account_id,
        Service=service,
        ResourceIdentifier=resource_identifier,
        Policy=""
    ), statement_count=1)
    
    assert response == expected
    