# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger
from mypy_boto3_sesv2.type_defs import IdentityInfoTypeDef

import policy_explorer.policy_explorer_model as model
from aws.services.simple_email_service_v2 import SimpleEmailServiceV2
from policy_explorer.step_functions_lambda.utils import DenormalizePolicyDetailsIntoDynamoDBItems, scan_regions
from policy_explorer.step_functions_lambda.split_arn_to_policy_details import get_policy_details_from_arn
from aws.utils.get_partition import partition_name_for_current_region


class SESIdentityPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.DynamoDBPolicyItem]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.DynamoDBPolicyItem]:
        self.logger.info(f"Scanning SES Identity Policies in {region}")
        ses_client = SimpleEmailServiceV2(self.account_id, region)
        ses_identity_data: list[IdentityInfoTypeDef] = ses_client.list_email_identities()
        ses_identities_policies = self._get_ses_policies(ses_identity_data, ses_client, region)
        ses_identities_policies_dynamodb_items = []
        for ses_identity_policy in ses_identities_policies:
            if ses_identity_policy.get('Policy'):
                ses_identities_policies_dynamodb_items.extend(DenormalizePolicyDetailsIntoDynamoDBItems(self.event).model(ses_identity_policy))   
        return ses_identities_policies_dynamodb_items

    def _get_ses_policies(self, ses_data: list[IdentityInfoTypeDef], ses_client, region) -> list[model.PolicyDetails]:
        ses_policies = []
        for ses in ses_data:

            policies: dict[str, str] = ses_client.get_email_identity_policies(
                ses['IdentityName']
            ).get('Policies')

            # create a map for each policy per identity
            for policy_name, policy in policies.items():
                resource_arn = f"arn:{partition_name_for_current_region()}:ses:{region}:{self.account_id}:{ses.get('IdentityType')}/{ses.get('IdentityName')}/{policy_name}"
                policy_details: model.PolicyDetails = get_policy_details_from_arn(resource_arn)
                policy_details.update({'PolicyType': model.PolicyType.RESOURCE_BASED_POLICY})
                policy_details.update({'Policy': policy})
                ses_policies.append(policy_details)
        return ses_policies
