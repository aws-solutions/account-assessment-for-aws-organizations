#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json

import boto3
from aws_lambda_powertools import Logger
from moto import mock_aws

from policy_explorer.policy_explorer_model import PolicyType, PolicyDetails
from policy_explorer.step_functions_lambda.scan_media_store_policy import MediaStorePolicy
from tests.test_policy_explorer.mock_data import event, mock_policies

logger = Logger(level="info")


@mock_aws
def test_no_mediastore_keys():
    # ACT
    response = MediaStorePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 0


@mock_aws
def test_mediastore_key_no_policy(mocker):
    # ARRANGE
    for region in event['Regions']:
        media_store_client = boto3.client("mediastore", region_name=region)
        for policy_object in mock_policies:
            if policy_object.get('MockResourceName'):
                media_store_client.create_container(
                    ContainerName=policy_object.get('MockResourceName'),
                    Tags=[{"Key": "customer"}]
                )
                if policy_object.get('MockPolicy'):
                    media_store_client.put_container_policy(
                        ContainerName=policy_object.get('MockResourceName'),
                        Policy=json.dumps(policy_object.get('MockPolicy'))
                    )

    def mock_get_policy_details_from_arn(resource_arn: str):
        return PolicyDetails(
            PolicyType=None,
            Region="us-east-1",
            AccountId=999999999999,
            Service="mediastore",
            ResourceIdentifier="container/test-for-aa",
            Policy=None
        )
    mocker.patch(
        "policy_explorer.step_functions_lambda.scan_media_store_policy.get_policy_details_from_arn",
        mock_get_policy_details_from_arn
    )
    
    def mock_container_policy(arg1: str, container_name: str):
        return {"Policy":"{\"Version\":\"2012-10-17\",\"Id\":\"default\",\"Statement\":[{\"Sid\":\"StackSet-account-assessment-14ba7782-f201-4-ApiAccountAssessmentForAWSOrganisationsApid-flUBFfVaA0f3\",\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"apigateway.amazonaws.com\"},\"Action\":\"lambda:InvokeFunction\",\"Resource\":\"arn:aws:lambda:us-east-2:111111111111:function:StackSet-account-assessme-DelegatedAdminsRead591DC-rhv1zfo76L1z\",\"Condition\":{\"ArnLike\":{\"AWS:SourceArn\":\"arn:aws:execute-api:us-east-2:111111111111:p2ut8bkpyi/test-invoke-stage/GET/delegated-admins\"}}},{\"Sid\":\"StackSet-account-assessment-14ba7782-f201-4-ApiAccountAssessmentForAWSOrganisationsApid-vVq9XsCs32U2\",\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"apigateway.amazonaws.com\"},\"Action\":\"lambda:InvokeFunction\",\"Resource\":\"arn:aws:lambda:us-east-2:111111111111:function:StackSet-account-assessme-DelegatedAdminsRead591DC-rhv1zfo76L1z\",\"Condition\":{\"ArnLike\":{\"AWS:SourceArn\":\"arn:aws:execute-api:us-east-2:111111111111:p2ut8bkpyi/prod/GET/delegated-admins\"}}}]}"}
    
    mocker.patch(
        "aws.services.media_store.MediaStore.get_container_policy",
        mock_container_policy
    )
    response = MediaStorePolicy(event).scan()
    logger.info(response)

    # ASSERT
    assert len(list(response)) == 44
    for resource in response:
       assert resource.get('PartitionKey') == PolicyType.RESOURCE_BASED_POLICY.value
