# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# !/bin/python
from os import getenv
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError
from mypy_boto3_organizations.client import OrganizationsClient
from mypy_boto3_organizations.type_defs import ListDelegatedAdministratorsResponseTypeDef, \
    DelegatedAdministratorTypeDef, ListDelegatedServicesForAccountResponseTypeDef, DelegatedServiceTypeDef, \
    EnabledServicePrincipalTypeDef, AccountTypeDef, ListAccountsResponseTypeDef, PolicySummaryTypeDef, \
    DescribePolicyResponseTypeDef, ListPoliciesResponseTypeDef

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session

NEXT_TOKEN_RETURNED = "Next Token Returned"


class Organizations:
    def __init__(self):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        management_account_id = self._get_management_account_id()
        role_name = getenv('ORG_MANAGEMENT_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {management_account_id}")
        management_credentials = SecurityTokenService().assume_role_by_name(management_account_id, role_name)
        boto_session = Boto3Session('organizations', credentials=management_credentials)
        self.org_client: OrganizationsClient = boto_session.get_client()

    def _get_management_account_id(self) -> str:
        try:
            boto_session = Boto3Session('organizations')
            org_client: OrganizationsClient = boto_session.get_client()
            response = org_client.describe_organization()
            master_account_id = response.get('Organization').get('MasterAccountId')
            self.logger.debug(f"Management Account Id: {master_account_id}")
            return master_account_id
        except ClientError as err:
            self.logger.error(err)
            raise

    def get_account_ids_in_org_units(self, org_unit_ids: list[str]) -> list[str]:
        accounts_ids = list(
            account['Id']
            for org_unit in org_unit_ids
            for account in self._get_accounts_for_parent(org_unit)
        )
        return accounts_ids

    def _get_accounts_for_parent(self, parent):
        try:
            accounts = []
            response = self.org_client.list_accounts_for_parent(ParentId=parent)

            accounts.extend(response.get('Accounts', []))
            next_token = response.get('NextToken', None)

            while next_token is not None:
                self.logger.debug(f"{NEXT_TOKEN_RETURNED}: {next_token})")
                response = self.org_client.list_accounts_for_parent(
                    ParentId=parent,
                    NextToken=next_token
                )
                accounts.extend(response.get('Accounts', []))
                next_token = response.get('NextToken', None)
            return accounts
        except ClientError as err:
            self.logger.error(err)
            raise

    def list_active_account_ids(self) -> list[str]:
        org_accounts = self.list_accounts()
        return list(account['Id']
                    for account in org_accounts
                    if account.get('Status') == 'ACTIVE')

    def list_accounts(self) -> list[AccountTypeDef]:
        try:
            response: ListAccountsResponseTypeDef = self.org_client.list_accounts()

            accounts = response.get('Accounts', [])
            next_token = response.get('NextToken', None)

            while next_token is not None:
                self.logger.debug(f"{NEXT_TOKEN_RETURNED}: {next_token})")
                response = self.org_client.list_accounts(
                    NextToken=next_token
                )
                self.logger.info("Extending Account List")
                accounts.extend(response.get('Accounts', []))
                next_token = response.get('NextToken', None)

            return accounts
        except ClientError as err:
            self.logger.error(err)
            raise

    def list_delegated_administrators(self) -> list[DelegatedAdministratorTypeDef]:
        try:
            response: ListDelegatedAdministratorsResponseTypeDef \
                = self.org_client.list_delegated_administrators()

            delegated_admins: list[DelegatedAdministratorTypeDef] = response.get('DelegatedAdministrators', [])
            next_token = response.get('NextToken', None)

            while next_token is not None:
                self.logger.debug(f"{NEXT_TOKEN_RETURNED}: {next_token})")
                response = self.org_client.list_delegated_administrators(
                    NextToken=next_token
                )
                self.logger.info("Extending Delegated Administrators List")
                delegated_admins.extend(response.get('DelegatedAdministrators', []))
                next_token = response.get('NextToken', None)

            self.logger.debug(delegated_admins)
            return delegated_admins

        except ClientError as err:
            self.logger.error(err)
            raise

    def list_delegated_services_for_account(self, account_id: str) -> list[DelegatedServiceTypeDef]:
        try:
            response: ListDelegatedServicesForAccountResponseTypeDef = \
                self.org_client.list_delegated_services_for_account(AccountId=account_id)

            delegated_services: list[DelegatedServiceTypeDef] = response.get('DelegatedServices', [])
            next_token = response.get('NextToken', None)

            while next_token is not None:
                self.logger.debug(f"{NEXT_TOKEN_RETURNED}: {next_token})")
                response = self.org_client.list_delegated_services_for_account(
                    AccountId=account_id,
                    NextToken=next_token
                )
                self.logger.info("Extending Delegated Services List")
                delegated_services.extend(response.get('DelegatedServices', []))
                next_token = response.get('NextToken', None)
            return delegated_services

        except ClientError as err:
            self.logger.error(err)
            raise

    def list_aws_service_access_for_organization(self) -> list[EnabledServicePrincipalTypeDef]:
        try:
            response = self.org_client.list_aws_service_access_for_organization()

            enabled_service_principals = response.get('EnabledServicePrincipals', [])
            next_token = response.get('NextToken', None)

            while next_token is not None:
                self.logger.debug(f"{NEXT_TOKEN_RETURNED}: {next_token})")
                response = self.org_client.list_aws_service_access_for_organization(
                    NextToken=next_token
                )
                self.logger.info("Extending Enabled Service Principals List")
                enabled_service_principals.extend(response.get('EnabledServicePrincipals', []))
                next_token = response.get('NextToken', None)
            return enabled_service_principals

        except ClientError as err:
            self.logger.error(err)
            raise
    

    def list_policies(self) -> list[PolicySummaryTypeDef]:
        try:
            response: ListPoliciesResponseTypeDef = self.org_client.list_policies(
                Filter='SERVICE_CONTROL_POLICY'
                )
            policies_summary_list: list[PolicySummaryTypeDef]  = response.get('Policies', [])
            next_token = response.get('NextToken', None)
            
            while next_token is not None:
                response = self.org_client.list_policies(
                    Filter='SERVICE_CONTROL_POLICY',
                    NextToken=next_token
                )
                policies_summary_list.extend(response.get('Policies', []))
                next_token = response.get('NextToken', None)
            return policies_summary_list
        except ClientError as err:
            self.logger.error(err)
            raise


    def describe_policy(self, policy_id: str) -> DescribePolicyResponseTypeDef:
        try: 
            response: DescribePolicyResponseTypeDef = self.org_client.describe_policy(
                PolicyId=policy_id
            )
            policy = response.get('Policy')
            if 'Content' in policy:
                return policy.get('Content')
        except ClientError as err:
            self.logger.error(err)
            raise