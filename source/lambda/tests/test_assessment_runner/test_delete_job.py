# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
import uuid

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_dynamodb.service_resource import Table

from assessment_runner import api_router
from assessment_runner.jobs_repository import JobsRepository
from delegated_admins.delegated_admins_repository import DelegatedAdminsRepository
from tests.test_utils.testdata_factory import job_create_request, delegated_admin_create_request, \
    trusted_access_create_request
from trusted_access_enabled_services.trusted_services_repository import TrustedServicesRepository
from utils.api_gateway_lambda_handler import ApiGatewayResponse


def describe_delete_job():
    job_create_request_1 = job_create_request()
    job_create_request_2 = job_create_request()

    def test_that_it_fails_if_job_not_exist(job_history_table):
        # ARRANGE
        event = {"path": "/jobs/DELEGATED_ADMIN/" + uuid.uuid4().hex, "httpMethod": "DELETE"}

        # ACT
        result: ApiGatewayResponse = api_router.lambda_handler(event, LambdaContext())

        # ASSERT
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert body['Error'] == "Job not found"

    def test_that_it_fails_if_job_active(job_history_table):
        # ARRANGE
        repository = JobsRepository()
        job = repository.create_job(job_create_request_1)

        event = {"path": f"/jobs/{job['AssessmentType']}/{job['JobId']}", "httpMethod": "DELETE"}

        # ACT
        result: ApiGatewayResponse = api_router.lambda_handler(event, LambdaContext())

        # ASSERT
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert body['Error'] == "Job is active"

        job_in_ddb = repository.get_job(job['AssessmentType'], job['JobId'])
        assert job_in_ddb == job

    def test_that_it_deletes_job_with_given_key(job_history_table,
                                                delegated_admin_table: Table):
        # ARRANGE
        repository = JobsRepository()

        job_create_request_2['JobStatus'] = 'SUCCESS'
        job2 = repository.create_job(job_create_request_2)

        event = {"path": f"/jobs/{job2['AssessmentType']}/{job2['JobId']}", "httpMethod": "DELETE"}

        # ACT
        result = api_router.lambda_handler(event, LambdaContext())

        # ASSERT
        assert result['statusCode'] == 200

        with pytest.raises(Exception):
            repository.get_job(job2['AssessmentType'], job2['JobId'])

    def test_that_it_deletes_delegated_admin_findings(job_history_table,
                                                      delegated_admin_table):
        # ARRANGE
        repository = JobsRepository()
        delegated_admins_repository = DelegatedAdminsRepository()
        job_create_request_2['JobStatus'] = 'SUCCESS'
        job = repository.create_job(job_create_request_2)

        item1 = delegated_admin_create_request('ssm.amazonaws.com', 'dev-account-id', job['JobId'])
        item2 = delegated_admin_create_request('guardduty.amazonaws.com', 'dev-account-id', job['JobId'])
        item3 = delegated_admin_create_request('guardduty.amazonaws.com', 'dev-2-account-id', job['JobId'])

        delegated_admins_repository.create_all([item1, item2, item3])

        assert delegated_admins_repository.get_delegated_admin(item1['ServicePrincipal'], item1['AccountId'])

        event = {"path": f"/jobs/{job['AssessmentType']}/{job['JobId']}", "httpMethod": "DELETE"}

        # ACT
        result = api_router.lambda_handler(event, LambdaContext())

        # ASSERT
        assert result['statusCode'] == 200

        with pytest.raises(Exception):
            # noinspection PyStatementEffect
            delegated_admins_repository.get_delegated_admin(item1['ServicePrincipal'], item1['AccountId'])
        with pytest.raises(Exception):
            # noinspection PyStatementEffect
            delegated_admins_repository.get_delegated_admin(item2['ServicePrincipal'], item2['AccountId'])
        with pytest.raises(Exception):
            # noinspection PyStatementEffect
            delegated_admins_repository.get_delegated_admin(item3['ServicePrincipal'], item3['AccountId'])

    def test_that_it_deletes_trusted_access_findings(job_history_table,
                                                     trusted_services_table):
        # ARRANGE
        repository = JobsRepository()
        job_create_request_2['JobStatus'] = 'SUCCESS'
        job_create_request_2['AssessmentType'] = 'TRUSTED_ACCESS'
        job = repository.create_job(job_create_request_2)
        repository.put_last_job_marker(job)

        item = trusted_access_create_request(service_principal="ssm.amazonaws.com", job_id=job['JobId'])
        trusted_services_repository = TrustedServicesRepository()
        trusted_access_model = trusted_services_repository.create_trusted_service(item)

        assert trusted_services_repository.get_trusted_service(trusted_access_model['ServicePrincipal'])

        event = {"path": f"/jobs/{job['AssessmentType']}/{job['JobId']}", "httpMethod": "DELETE"}

        # ACT
        result = api_router.lambda_handler(event, LambdaContext())

        # ASSERT
        assert result['statusCode'] == 200
        assert repository.get_last_job_marker('TRUSTED_ACCESS') is None

        with pytest.raises(Exception):
            # noinspection PyStatementEffect
            trusted_services_repository.get_trusted_service(trusted_access_model['ServicePrincipal'])
