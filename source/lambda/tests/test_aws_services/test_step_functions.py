#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os
import re
from datetime import datetime

from moto import mock_aws
from moto.core import DEFAULT_ACCOUNT_ID as ACCOUNT_ID

from aws.services.step_functions import StepFunctions


@mock_aws
def test_state_machine_start_execution(stepfunctions_client, organizations_setup):
    # ARRANGE
    region = "us-east-1"
    uuid_regex = "[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"
    expected_exec_name = (
        f"arn:aws:states:{region}:{ACCOUNT_ID}:execution:name:{uuid_regex}"
    )
    state_machine = _setup_simple_state_machine(stepfunctions_client)

    # ACT
    machine_input = {}
    execution = StepFunctions().start_execution(
        state_machine["stateMachineArn"],
        machine_input
    )

    # ASSERT
    assert execution["ResponseMetadata"]["HTTPStatusCode"] == 200
    assert re.match(expected_exec_name, execution["executionArn"])
    assert type(execution["startDate"]) == datetime


def _setup_simple_state_machine(stepfunctions_client):
    simple_definition = (
        '{"Comment": "Mock Amazon States Language Definition",'
        '"StartAt": "DefaultState",'
        '"States": '
        '{"DefaultState": {"Type": "Fail","Error": "DefaultStateError","Cause": "No Matches!"}}}'
    )
    state_machine = stepfunctions_client.create_state_machine(
        name="name", definition=str(simple_definition), roleArn=_get_default_role()
    )
    print(state_machine["stateMachineArn"])
    os.environ['SCAN_RESOURCE_POLICY_STATE_MACHINE_ARN'] = state_machine["stateMachineArn"]
    return state_machine


def _get_default_role():
    return f"arn:aws:iam::{ACCOUNT_ID}:role/unknown_sf_role"
