# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests():
    os.environ['LOG_LEVEL'] = 'debug'
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['SOLUTION_VERSION'] = "v1.0.0"
    os.environ['ORG_MANAGEMENT_ROLE_NAME'] = 'execution-role-name'
    os.environ['SPOKE_ROLE_NAME'] = 'AccountAssessment-Spoke-ExecutionRole'
    os.environ[
        'REGIONS'] = 'eu-north-1,ap-south-1, eu-west-3, eu-west-2,eu-west-1,ap-northeast-3,ap-northeast-2,ap-northeast-1,sa-east-1,ca-central-1,ap-southeast-1,ap-southeast-2,eu-central-1,us-east-1,us-east-2,us-west-1,us-west-2'
    os.environ['SERVICE_NAMES'] = 's3, config, cloudformation'
