#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from os import getenv

from aws_lambda_powertools import Logger, Tracer
from assessment_runner.assessment_runner import write_task_failure
from aws.services.security_token_service import SecurityTokenService
from policy_explorer.policy_explorer_model import AccountValidationRequestModel, \
    AccountValidationResponseModel, ValidationType
from mypy_boto3_sts.type_defs import CredentialsTypeDef
from aws.services.account import AccountService

logger = Logger(getenv('LOG_LEVEL'))
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
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
    
    def get_regions_for_account(self, credentials: CredentialsTypeDef, account_id: str) -> list[str]:
        account_service: AccountService = AccountService(credentials=credentials)
        return account_service.get_regions(account_id=account_id)
        
    def check_account_access_permission(self) -> AccountValidationResponseModel:
        try:
            account_credentials = SecurityTokenService().assume_role_by_name(self.account_id, self.role_name)
            sts = SecurityTokenService(credentials=account_credentials)
            if sts.get_caller_identity().get('Account') == self.account_id:
                self.logger.info("Account IDs matched - Validation Successful.")
                # Get Regions for the account
                regions = self.get_regions_for_account(credentials=account_credentials, account_id=self.account_id)
                self.logger.debug(f"Regions for the account {self.account_id} are {regions}")
                return {
                    "Validation": str(ValidationType.SUCCEEDED.value),
                    "ServicesToScanForAccount": self.service_names,
                    "Regions": regions
                }
            else:
                self.logger.info("Account Ids didn't match skip this account")
                write_task_failure(self.job_id,
                                   'POLICY_EXPLORER',
                                   self.account_id,
                                   None,
                                   None,
                                   "Access Validation Failed: Unable to assume role in this account.")
                return {
                    "Validation": str(ValidationType.FAILED.value),
                    "ServicesToScanForAccount": [],
                    "Regions": []
                }
        except Exception as err:
            logger.error(f'Logging failure in DDB: {err}')
            write_task_failure(
                self.job_id,
                'POLICY_EXPLORER',
                self.account_id,
                None,
                None,
                str(err))
            return {
                "Validation": str(ValidationType.FAILED.value),
                "ServicesToScanForAccount": [],
                "Regions": []
            }
