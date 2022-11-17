# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import uuid
from datetime import datetime
from typing import List

from assessment_runner.job_model import JobStatus, JobCreateRequest
from delegated_admins.delegated_admin_model import DelegatedAdminModel
from resource_based_policy.resource_based_policy_model import ResourceBasedPolicyResponseModel
from resource_based_policy.supported_configuration.scan_configuration_model import ScanConfigCreateRequest
from trusted_access_enabled_services.trusted_access_model import TrustedAccessCreateRequest


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


def scan_config_create_request(
        account_ids: List[str],
        configuration_name: str = uuid.uuid4().hex,
) -> ScanConfigCreateRequest:
    return {
        "AccountIds": account_ids,
        "Regions": [],
        "ServiceNames": [],
        "ConfigurationName": configuration_name
    }
