#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
import traceback
from datetime import datetime, timezone
from os import getenv
from typing import List, Iterable

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_organizations.type_defs import DelegatedAdministratorTypeDef, DelegatedServiceTypeDef

from assessment_runner.assessment_runner import AssessmentRunner, SynchronousScanStrategy
from assessment_runner.job_model import AssessmentType
from aws.services.organizations import Organizations
from delegated_admins.delegated_admin_model import DelegatedAdminCreateRequest
from delegated_admins.delegated_admins_repository import DelegatedAdminsRepository
from metrics.solution_metrics import SolutionMetrics
from utils.api_gateway_lambda_handler import ApiGatewayResponse, GenericApiGatewayEventHandler, default_headers
from utils.decimal_json_encoder import DecimalJsonEncoder

logger = Logger(getenv('LOG_LEVEL'))
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext) -> ApiGatewayResponse:
    try:
        return GenericApiGatewayEventHandler().handle_and_create_response(
            event,
            context,
            AssessmentRunner(DelegatedAdminsStrategy()).run_assessment
        )
    except Exception as error:
        logger.error(f"Error: {error}")
        logger.error(traceback.format_exc())
        error_type = type(error).__name__
        body = {
            "Error": error_type,
            "Message": "An unexpected error occurred. Inspect CloudWatch logs for more information.",
            "Timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
        return {
            'statusCode': 400,
            'body': json.dumps(body, cls=DecimalJsonEncoder),
            'headers': default_headers,
        }


class DelegatedAdminsStrategy(SynchronousScanStrategy):
    """
    Search the current account's aws organization
    for delegated admin accounts and their related service principal
    """

    def __init__(self):
        self.job_id = None
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.organization = Organizations()

    def assessment_type(self) -> str: return str(AssessmentType.DELEGATED_ADMIN.value)

    def scan(self, job_id, request_body) -> List[DelegatedAdminCreateRequest]:
        self.job_id = job_id
        delegated_admin_accounts: List[DelegatedAdministratorTypeDef] \
            = self.organization.list_delegated_administrators()
        self.logger.info(f"Found {len(delegated_admin_accounts)} accounts designated as delegated administrators.")

        delegated_services_and_accounts: List[DelegatedAdminCreateRequest] = []
        for account in delegated_admin_accounts:
            enabled_services_per_account = self._find_delegated_services(account)
            delegated_services_and_accounts.extend(enabled_services_per_account)

        self.logger.debug(f"Merged Delegated Admin Account and Service: "
                          f"{delegated_services_and_accounts}")

        return delegated_services_and_accounts

    def _find_delegated_services(self, account) -> Iterable[DelegatedAdminCreateRequest]:
        self.logger.info(f"Finding delegated services for {account.get('Id')}")
        self.logger.debug(f"Delegated Account: {account}")
        delegated_services = self.organization.list_delegated_services_for_account(
            account.get('Id')
        )
        self.logger.debug(f"Delegated Services: {delegated_services}")
        return list(self._denormalize_to_delegated_admin_model(account, service) for service in delegated_services)

    def _denormalize_to_delegated_admin_model(
            self,
            account: DelegatedAdministratorTypeDef,
            service: DelegatedServiceTypeDef
    ) -> DelegatedAdminCreateRequest:
        model: DelegatedAdminCreateRequest = {
            'AccountId': account['Id'],
            'ServicePrincipal': service['ServicePrincipal'],
            'Arn': account['Arn'],
            'Email': account['Email'],
            'Name': account['Name'],
            'Status': account['Status'],
            'JoinedMethod': account['JoinedMethod'],
            'JoinedTimestamp': account['JoinedTimestamp'].isoformat(),
            'DelegationEnabledDate': account['DelegationEnabledDate'].isoformat(),
            'JobId': self.job_id,
            'AssessedAt': datetime.now().isoformat()
        }
        self.logger.debug(model)
        return model

    def write(self, delegated_admins: List[DelegatedAdminCreateRequest]):
        findings = DelegatedAdminsRepository().create_all(delegated_admins)
        SolutionMetrics().send_scan_metrics(self.assessment_type(), findings)
