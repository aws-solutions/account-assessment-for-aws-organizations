#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from moto import mock_aws
from mypy_boto3_ssm_contacts.type_defs import ContactTypeDef

from policy_explorer.policy_explorer_model import PolicyType
from policy_explorer.step_functions_lambda.scan_ssm_contacts_policy import \
    SSMContactsPolicy
from tests.test_policy_explorer.mock_data import event

logger = Logger(level='info')


@mock_aws
def test_mock_ssm_contacts_scan_policy_no_policies(mocker):
    # ARRANGE
    mock_ssm_contacts(mocker)

    # ACT
    response = SSMContactsPolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert response == []


@mock_aws
def test_mock_ssm_contacts_scan_policy(mocker):
    # ARRANGE
    list_contacts_response: list[ContactTypeDef] = [
        {
            "ContactArn": "arn:aws:ssm-contacts:*:111122223333:contact/mycontact",
            "Alias": "mycontact",
            "Type": "PERSONAL"
        }
    ]
    

    mock_ssm_contacts(mocker, list_contacts_response=list_contacts_response, get_contact_policies_response=[])

    # ACT
    response = SSMContactsPolicy(event).scan()
    logger.info(f"RESPONSE: {response}")

    # ASSERT
    assert len(list(response)) == 2
    for resource in response:
        assert resource.get('PartitionKey') == PolicyType.RESOURCE_BASED_POLICY.value

def mock_ssm_contacts(mocker, list_contacts_response=None, get_contact_policies_response=None):
    # ARRANGE
    if not list_contacts_response:
        list_contacts_response = []
    
    if not get_contact_policies_response:
        get_contact_policies_response = []

    def mock_list_contacts(self):
        return list_contacts_response
    
    mocker.patch(
        "aws.services.ssm_contacts.SSMContacts.list_contacts",
        mock_list_contacts
    )


    def mock_get_contact_policy(self, contact_arn: str):
        if (contact_arn == "arn:aws:ssm-contacts:*:111122223333:contact/mycontact"):
         return "{\"Version\":\"2012-10-17\",\"Id\":\"aasd\",\"Statement\":[{\"Sid\":\"PrincipalAccess\",\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"arn:aws:iam:*:111122223333:mycontact\"},\"Action\":[\"ssm-contacts:GetContact\",\"ssm-contacts:StartEngagement\",\"ssm-contacts:DescribeEngagement\",\"ssm-contacts:ListPagesByContact\"],\"Resource\":[\"arn:aws:ssm-contacts:*:111122223333:contact/mycontact\",\"arn:aws:ssm-contacts:*:111122223333:engagement/mycontact/*\"],\"Condition\": {\"StringEquals\": {\"aws:PrincipalOrgID\":\"o-eci09zojnh\"}}}]}"
        
        else:
            return {'Error': 'There is no policy for registry default. Create a resource-based policy and try your request again.'}
    mocker.patch(
         "aws.services.ssm_contacts.SSMContacts.get_contact_policy",
        mock_get_contact_policy
    )