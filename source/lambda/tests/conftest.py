#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os
from os import environ

import boto3
import pytest
from aws_lambda_powertools import Logger
from moto import mock_aws

from utils.base_repository import Clock

logger = Logger(loglevel='info')


@pytest.fixture(scope='module')
def aws_credentials():
    """Mocked AWS Credentials for moto"""
    environ['AWS_ACCESS_KEY_ID'] = 'testing'
    environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    environ['AWS_SECURITY_TOKEN'] = 'testing'
    environ['AWS_SESSION_TOKEN'] = 'testing'
    environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    environ['AWS_REGION'] = 'us-east-1'


@pytest.fixture
def org_client(aws_credentials):
    """Organizations Mock Client"""
    with mock_aws():
        connection = boto3.client("organizations", region_name="us-east-1")
        yield connection


@pytest.fixture(scope='module')
def dynamodb_client_resource(aws_credentials):
    """DDB Mock Client"""
    with mock_aws():
        connection = boto3.resource("dynamodb")
        yield connection


@pytest.fixture(scope='module')
def stepfunctions_client(aws_credentials):
    with mock_aws():
        connection = boto3.client("stepfunctions", region_name="us-east-1")
        yield connection


@pytest.fixture(scope='module')
def iam_client(aws_credentials):
    with mock_aws():
        connection = boto3.client("iam", region_name="us-east-1")
        yield connection


@pytest.fixture(scope='module')
def s3_client(aws_credentials):
    with mock_aws():
        connection = boto3.client("s3", region_name="us-east-1")
        yield connection


@pytest.fixture(scope='module')
def s3_client_resource(aws_credentials):
    with mock_aws():
        connection = boto3.resource("s3", region_name="us-east-1")
        yield connection


@pytest.fixture(scope='module')
def glacier_client(aws_credentials):
    with mock_aws():
        connection = boto3.client("glacier", region_name="us-east-1")
        yield connection


@pytest.fixture
def organizations_setup(org_client):
    dev_map = {
        "AccountName": "Developer1",
        "AccountEmail": "dev@mock",
        "OUName": "Dev"
    }
    dev_map_2 = {
        "AccountName": "Developer1-SuperSet",
        "AccountEmail": "dev-2@mock",
        "OUName": "Dev"
    }
    prod_map = {
        "AccountName": "Production1",
        "AccountEmail": "prod@mock",
        "OUName": "Prod"
    }

    test_map = {
        "AccountName": "Testing1",
        "AccountEmail": "test@mock",
        "OUName": "Test"
    }
    # create organization
    org_client.create_organization(FeatureSet="ALL")
    root_id = org_client.list_roots()["Roots"][0]["Id"]

    # create accounts
    dev_account_id = org_client.create_account(
        AccountName=dev_map['AccountName'],
        Email=dev_map['AccountEmail'])["CreateAccountStatus"]["AccountId"]
    dev_account_id_2 = org_client.create_account(
        AccountName=dev_map_2['AccountName'],
        Email=dev_map_2['AccountEmail'])["CreateAccountStatus"]["AccountId"]
    test_account_id = org_client.create_account(
        AccountName=test_map['AccountName'],
        Email=test_map['AccountEmail'])["CreateAccountStatus"]["AccountId"]
    prod_account_id = org_client.create_account(
        AccountName=prod_map['AccountName'],
        Email=prod_map['AccountEmail'])["CreateAccountStatus"]["AccountId"]

    # create org units
    dev_resp = org_client.create_organizational_unit(ParentId=root_id,
                                                     Name=dev_map['OUName'])
    dev_ou_id = dev_resp["OrganizationalUnit"]["Id"]
    test_resp = org_client.create_organizational_unit(ParentId=root_id,
                                                      Name=test_map['OUName'])
    test_ou_id = test_resp["OrganizationalUnit"]["Id"]
    prod_resp = org_client.create_organizational_unit(ParentId=root_id,
                                                      Name=prod_map['OUName'])
    prod_ou_id = prod_resp["OrganizationalUnit"]["Id"]

    # move accounts
    org_client.move_account(
        AccountId=dev_account_id, SourceParentId=root_id,
        DestinationParentId=dev_ou_id
    )
    org_client.move_account(
        AccountId=dev_account_id_2, SourceParentId=root_id,
        DestinationParentId=dev_ou_id
    )
    org_client.move_account(
        AccountId=test_account_id, SourceParentId=root_id,
        DestinationParentId=test_ou_id
    )
    org_client.move_account(
        AccountId=prod_account_id, SourceParentId=root_id,
        DestinationParentId=prod_ou_id
    )
    yield {
        'dev_account_id': dev_account_id,
        'dev_account_id_2': dev_account_id_2,
        'test_account_id': test_account_id,
        'prod_account_id': prod_account_id,
        'dev_ou_id': dev_ou_id
    }


# setup mock dynamodb table
@pytest.fixture()
def delegated_admin_table(dynamodb_client_resource):
    table_name = 'DelegatedAdmins'
    os.environ["TABLE_DELEGATED_ADMIN"] = table_name
    os.environ["COMPONENT_TABLE"] = table_name

    yield from _create_table(dynamodb_client_resource, table_name)


@pytest.fixture()
def trusted_services_table(dynamodb_client_resource):
    table_name = 'TrustedServices'
    os.environ["TABLE_TRUSTED_ACCESS"] = table_name
    os.environ["COMPONENT_TABLE"] = table_name

    yield from _create_table(dynamodb_client_resource, table_name)


@pytest.fixture()
def resource_based_policies_table(dynamodb_client_resource):
    table_name = 'ResourceBasedPolicies'
    os.environ["COMPONENT_TABLE"] = table_name

    yield from _create_table(dynamodb_client_resource, table_name)

@pytest.fixture()
def policy_explorer_table(dynamodb_client_resource):
    table_name = 'PolicyExplorer'
    os.environ["COMPONENT_TABLE"] = table_name

    yield from _create_table(dynamodb_client_resource, table_name)


@pytest.fixture()
def job_history_table(dynamodb_client_resource):
    table_name = 'JobHistory'
    os.environ["TABLE_JOBS"] = table_name

    yield from _create_table(dynamodb_client_resource, table_name)


def _create_table(dynamodb_client_resource, table_name):
    logger.info("ARRANGE: Creating Table " + table_name)

    table = dynamodb_client_resource.create_table(
        TableName=table_name,
        KeySchema=[
            {
                "AttributeName": "PartitionKey",
                "KeyType": "HASH"
            },
            {
                "AttributeName": "SortKey",
                "KeyType": "RANGE"
            }
        ],
        AttributeDefinitions=[
            {
                "AttributeName": "PartitionKey",
                "AttributeType": "S"
            },
            {
                "AttributeName": "SortKey",
                "AttributeType": "S"
            },
            {
                "AttributeName": "JobId",
                "AttributeType": "S"
            }
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5
        },
        GlobalSecondaryIndexes=[{
            'IndexName': 'JobId',
            'KeySchema': [
                {
                    'AttributeName': 'JobId',
                    'KeyType': 'HASH'
                },
            ],
            'Projection': {
                'ProjectionType': 'ALL',
            },
        }],
    )
    yield table
    logger.info("CLEANUP: Deleting Table")
    table.delete()


@pytest.fixture()
def freeze_clock(mocker):
    # Make Clock return constant 0 as current time
    mocker.patch.object(Clock, 'current_time_in_ms', return_value=0)
