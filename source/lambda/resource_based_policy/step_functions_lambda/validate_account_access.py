# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv

from aws_lambda_powertools import Logger, Tracer
from assessment_runner.assessment_runner import write_task_failure
from aws.services.security_token_service import SecurityTokenService
from resource_based_policy.resource_based_policy_model import AccountValidationRequestModel, \
    AccountValidationResponseModel, ValidationType

logger = Logger(getenv('LOG_LEVEL'))
tracer = Tracer()


@tracer.capture_lambda_handler
def lambda_handler(event: AccountValidationRequestModel, _context) -> AccountValidationResponseModel:
    logger.debug(event)
    return ValidateAccountAccess(event).check_account_access_permission()


class ValidateAccountAccess:
    """
    Validate accounts provided in the event. Mark them invalid to skip them in State Machine if we can't access the
    account.
    """

    def __init__(self, event: AccountValidationRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.role_name = getenv('SPOKE_ROLE_NAME')
        self.service_names = event['ServiceNames']
        self.account_id = event['AccountId']
        self.job_id = event['JobId']

    def check_account_access_permission(self) -> AccountValidationResponseModel:
        try:
            account_credentials = SecurityTokenService().assume_role_by_name(self.account_id, self.role_name)
            sts = SecurityTokenService(credentials=account_credentials)
            if sts.get_caller_identity().get('Account') == self.account_id:
                self.logger.info("Account IDs matched - Validation Successful.")
                return {
                    "Validation": str(ValidationType.SUCCEEDED.value),
                    "ServicesToScanForAccount": self.service_names
                }
            else:
                self.logger.info("Account Ids didn't match skip this account")
                write_task_failure(self.job_id,
                                   'RESOURCE_BASED_POLICY',
                                   self.account_id,
                                   None,
                                   None,
                                   "Access Validation Failed: Unable to assume role in this account.")
                return {
                    "Validation": str(ValidationType.FAILED.value),
                    "ServicesToScanForAccount": []
                }
        except Exception as err:
            logger.error(f'Logging failure in DDB: {err}')
            write_task_failure(
                self.job_id,
                'RESOURCE_BASED_POLICY',
                self.account_id,
                None,
                None,
                str(err))
            return {
                "Validation": str(ValidationType.FAILED.value),
                "ServicesToScanForAccount": []
            }
