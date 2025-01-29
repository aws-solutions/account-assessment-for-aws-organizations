#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import uuid
from datetime import datetime

from aws_lambda_powertools.utilities.typing import LambdaContext

from assessment_runner.job_model import JobStatus, JobCreateRequest
from delegated_admins.delegated_admin_model import DelegatedAdminModel
from policy_explorer.policy_explorer_model import DynamoDBPolicyItem
from resource_based_policy.resource_based_policy_model import ResourceBasedPolicyResponseModel
from trusted_access_enabled_services.trusted_access_model import TrustedAccessCreateRequest


class TestLambdaContext(LambdaContext):
    aws_request_id = 'abcdef'
    invoked_function_arn = 'foo'
    function_name = 'test'
    function_version = 'test'
    memory_limit_in_mb = '512'
    log_stream_name = 'baz'

def job_create_request(
        assessment_type: str = 'DELEGATED_ADMIN',
        job_status: str = str(JobStatus.ACTIVE.value)
) -> JobCreateRequest:
    return {
        'AssessmentType': assessment_type,
        'StartedAt': datetime.now().isoformat(),
        'StartedBy': 'John.Doe@example.com',
        'JobStatus': job_status,
    }


def delegated_admin_create_request(
        service_principal: str,
        account_id: str,
        job_id: str = uuid.uuid4().hex
) -> DelegatedAdminModel:
    return {
        'JobId': job_id,
        'AssessedAt': datetime.now().isoformat(),
        'Arn': 'arn:aws:organizations::mgmt-account:account/o-83oqsx31so/dev-account-id',
        'Email': 'dev3@mock',
        'Name': 'Developer2',
        'Status': 'ACTIVE',
        'JoinedMethod': 'CREATED',
        'JoinedTimestamp': '2022-07-19T18:09:06.612913-04:01',
        'DelegationEnabledDate': '2022-07-19T18:09:06.626269-04:04',
        'AccountId': account_id,
        'ServicePrincipal': service_principal}


def trusted_access_create_request(
        service_principal: str,
        job_id: str = uuid.uuid4().hex
) -> TrustedAccessCreateRequest:
    return {
        'DateEnabled': '2022-08-23T16:45:04.097853-04:00',
        'ServicePrincipal': service_principal,
        'JobId': job_id,
        'AssessedAt': '2022-08-23T16:45:04.112683'
    }


def resource_based_policies_create_request(
        service_name: str,
        region: str = 'global',
        job_id: str = uuid.uuid4().hex,
) -> ResourceBasedPolicyResponseModel:
    return {
        'AccountId': '111122223333',
        'ServiceName': service_name,
        'ResourceName': 'foo',
        'DependencyType': 'bar',
        'DependencyOn': 'baz',
        'JobId': job_id,
        'AssessedAt': '2022-08-23T16:45:04.112683',
        'Region': region
    }


def policy_create_request(
        policy_type: str,
        service: str = 'iam',
        account_id: str = 'dev-account-id',
        region: str = 'GLOBAL',
        action: str = '["sns:Subscribe", "sns:Unsubscribe"]',
        not_action: str = '["sns:Subscribe", "sns:Unsubscribe"]',
        resource: str = '["arn:aws:sns:*:*:aws-controltower-SecurityNotifications"]',
        not_resource: str = '["arn:aws:sns:*:*:aws-controltower-SecurityNotifications"]',
        effect: str = 'Deny',
        condition: str = '{"ArnNotLike": {"aws:PrincipalARN": "arn:aws:iam::*:role/AWSControlTowerExecution"}}',
        principal: str = '{"Service": "ssm.amazonaws.com"}',
        not_principal: str = '{"Service": "ssm.amazonaws.com"}',
        job_id: str = uuid.uuid4().hex
) -> DynamoDBPolicyItem:
    return {
        'PartitionKey': policy_type,
        'SortKey': f'{region}#{service}#{account_id}#policy/o-j8ayd8hori/service_control_policy/p-ao427iho#{uuid.uuid4().hex}',
        'AccountId': account_id,
        'Action': action,
        'NotAction': not_action,
        'Condition': condition,
        'Effect': effect,
        'Policy': '{"Version": "2012-10-17", "Statement": [{"Condition": {"ArnNotLike": {"aws:PrincipalARN": "arn:aws:iam::*:role/AWSControlTowerExecution"}}, "Action": ["sns:Subscribe", "sns:Unsubscribe"], "Resource": ["arn:aws:sns:*:*:aws-controltower-SecurityNotifications"], "Effect": "Deny", "Sid": "GRSNSSUBSCRIPTIONPOLICY"}]}',
        'Region': region,
        'Resource': resource,
        'NotResource': not_resource,
        'ResourceIdentifier': 'policy/o-j8ayd8hori/service_control_policy/p-ao427iho',
        'Service': service,
        'Principal': principal,
        'NotPrincipal': not_principal,
        'Sid': 'GRSNSSUBSCRIPTIONPOLICY',
        'JobId': job_id,
        'AssessedAt': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'ExpiresAt': 1715295627
    }
