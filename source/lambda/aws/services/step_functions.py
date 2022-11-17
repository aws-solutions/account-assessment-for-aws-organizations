# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# !/bin/python

import json
from os import getenv

from aws_lambda_powertools import Logger
from mypy_boto3_stepfunctions.type_defs import StartExecutionOutputTypeDef

from aws.utils.boto3_session import Boto3Session


class StepFunctions:
    def __init__(self, **kwargs):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        boto_session = Boto3Session('stepfunctions', **kwargs)
        self.state_machine_client = boto_session.get_client()

    def start_execution(self, state_machine_arn, state_machine_input) -> StartExecutionOutputTypeDef:
        try:
            in_str = json.dumps(state_machine_input)
            self.logger.info(f"Attempting to start state machine with arn {state_machine_arn} and input {in_str}")
            response = self.state_machine_client.start_execution(
                stateMachineArn=state_machine_arn,
                input=in_str
            )
            self.logger.info(f"State machine Execution ARN: {response['executionArn']}")
            return response
        except Exception as e:
            self.logger.error(e)
            raise
