# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import uuid

from aws_lambda_powertools import Logger
from moto import mock_sts

from trusted_access_enabled_services.scan_for_trusted_services import \
    TrustedAccessStrategy

logger = Logger(level="info")


@mock_sts
def test_zero_enabled_aws_service_access(organizations_setup):
    # ARRANGE
    job_id = str(uuid.uuid4())

    # ACT
    enabled_service_principals = TrustedAccessStrategy().scan(job_id, {})
    logger.info(f"Enabled AWS Services:"
                f" {enabled_service_principals}")

    assert len(enabled_service_principals) == 0

    # ASSERT
    for service in enabled_service_principals:
        logger.info(f"KEYS >>> {service.keys()}")
        assert "ServicePrincipal" in service.keys()
        assert "DateEnabled" in service.keys()
        assert "JobId" in service.keys()
        assert "AssessedAt" in service.keys()


@mock_sts
def test_enabled_aws_service_access(org_client, organizations_setup):
    # ARRANGE
    job_id = str(uuid.uuid4())
    org_client.enable_aws_service_access(ServicePrincipal="config.amazonaws.com")

    # ACT
    enabled_service_principals = TrustedAccessStrategy().scan(job_id, {})
    logger.info(f"Enabled AWS Services:"
                f" {enabled_service_principals}")

    assert len(enabled_service_principals) == 1

    # ASSERT
    for service in enabled_service_principals:
        assert "ServicePrincipal" in service.keys()
        assert "DateEnabled" in service.keys()
        assert "JobId" in service.keys()
        assert "AssessedAt" in service.keys()


@mock_sts
def test_multiple_enabled_aws_service_access(org_client, organizations_setup):
    # ARRANGE
    job_id = str(uuid.uuid4())
    org_client.enable_aws_service_access(ServicePrincipal="config.amazonaws.com")
    org_client.enable_aws_service_access(ServicePrincipal="ram.amazonaws.com")
    # ACT
    enabled_service_principals = TrustedAccessStrategy().scan(job_id, {})
    logger.info(f"Enabled AWS Services:"
                f" {enabled_service_principals}")

    assert len(enabled_service_principals) == 2

    # ASSERT
    for service in enabled_service_principals:
        assert "ServicePrincipal" in service.keys()
        assert "DateEnabled" in service.keys()
        assert "JobId" in service.keys()
        assert "AssessedAt" in service.keys()
