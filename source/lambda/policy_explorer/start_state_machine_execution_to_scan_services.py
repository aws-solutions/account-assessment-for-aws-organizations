#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
from os import getenv
from typing import Iterable, Dict

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

from assessment_runner.assessment_runner import AssessmentRunner, ScanStrategy, write_task_failure
from assessment_runner.job_model import AssessmentType
from aws.services.organizations import Organizations
from aws.services.step_functions import StepFunctions
from policy_explorer.policy_explorer_model import ScanModel, DynamoDBPolicyItem
from policy_explorer.policy_explorer_repository import PoliciesRepository
from policy_explorer.step_functions_lambda.scan_organizations_policy import ServiceControlPolicy
from policy_explorer.supported_configuration.supported_regions_and_services import SupportedServices

logger = Logger(getenv('LOG_LEVEL'))
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: Dict, context: LambdaContext) -> str:
    try:
        AssessmentRunner(ScanAllPoliciesStrategy()).run_assessment(event=None, _context=context)
    except Exception as error:
        print(f"Failed to start assessment runner {error}")
        raise error 
    return "started"

class ScanAllPoliciesStrategy(ScanStrategy):
    """
    search the active accounts in aws organizations and start state machine execution to assess resource based
    policies, iam policies, service control policies and iam role in-line policies in the accounts.
    """

    def __init__(self):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.state_machine_arn = getenv('SCAN_POLICIES_STATE_MACHINE_ARN')
        self.management_account_id = Organizations()._get_management_account_id()

    def assessment_type(self) -> str:
        return str(AssessmentType.POLICY_EXPLORER.value)
    
    def get_scan_config(self) -> ScanModel: 
        return {
                'AccountIds': Organizations().list_active_account_ids(),
                'ServiceNames':  SupportedServices.service_names()
                }

    def scan(self, job_id, request_body: Dict):
        
        self.logger.debug(f"Request body received {request_body}")

        state_machine_input = {
            'JobId': job_id,
            'Scan': self.get_scan_config()
        }
        self.logger.debug(state_machine_input)
        response_from_step_function = StepFunctions().start_execution(self.state_machine_arn, state_machine_input)
        
        #scan organization for scps
        try:
            self.logger.debug("Starting scan for service control policies")
            policies: Iterable[DynamoDBPolicyItem] = ServiceControlPolicy({
                'JobId': job_id, 
                'AccountId': self.management_account_id,
                'Regions': ['GLOBAL'],
                'ServiceName': 'organizations'}).scan()
            self.logger.debug(f"Service control policies {policies}")
            if policies:
                PoliciesRepository().create_all(policies)
        except ClientError as err:
            write_task_failure(
                job_id,
                'POLICY_EXPLORER',
                self.management_account_id,
                None,
                'organizations',
                json.dumps(err.response)
            )
        
        return response_from_step_function