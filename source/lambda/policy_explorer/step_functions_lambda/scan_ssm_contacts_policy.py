# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_ssm_contacts.type_defs import ContactTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.ssm_contacts import SSMContacts
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions 
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn


class SSMContactsPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)
    
    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning SSM Contact Policies in {region}")
        ssm_contacts_client = SSMContacts(self.account_id, region)
        contacts: list[ContactTypeDef] = ssm_contacts_client.list_contacts()
        contacts_and_policies: list[model.PolicyAnalyzerRequest] = self._get_contacts_and_policies(region, contacts, ssm_contacts_client)
        ssm_contact_policy_dynamodb_items = []
        for contact_policy in contacts_and_policies:
            if contact_policy.get('Policy'):
                ssm_contact_policy_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(contact_policy))
        return ssm_contact_policy_dynamodb_items

    def _get_contacts_and_policies(self, region: str , contacts: list[ContactTypeDef], ssm_contacts_client: SSMContacts) -> list[model.PolicyDetails]:
        return list(self._get_ssm_contact_policy(region, contact, ssm_contacts_client) for contact in contacts)
        
    def _get_ssm_contact_policy(self, region: str, contact: ContactTypeDef, ssm_contacts_client: SSMContacts)-> model.PolicyDetails:
        contact_policy: str = ssm_contacts_client.get_contact_policy(contact.get('ContactArn'))
        policy_details: model.PolicyDetails = get_policy_details_from_arn(contact.get('ContactArn'))
        policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
        policy_details.update({'Policy': contact_policy})
        policy_details.update({'Region': region})
        return policy_details