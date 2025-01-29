#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
from moto import mock_aws

from policy_explorer.policy_explorer_model import PolicyType
from policy_explorer.step_functions_lambda.scan_redshift_serverless_policy import RedshiftServerlessPolicy
from tests.test_policy_explorer.mock_data import event

logger = Logger(level='info', service="test_redshift_serverless")


@mock_aws
def test_mock_redshift_serverless_scan_policy(mocker):
    # ARRANGE
    mock_redshift_serverless(mocker)
    
    response = (event).scan()
    logger.info(response)
    
    assert response == []


@mock_aws
def test_mock_redshift_serverless_scan_policy(mocker):
    
    list_snapshots_response = [
        {
            'actualIncrementalBackupSizeInMegaBytes': 80.0, 
            'adminUsername': 'admin', 
            'backupProgressInMegaBytes': 80.0, 
            'currentBackupRateInMegaBytesPerSecond': 26.264, 
            'elapsedTimeInSeconds': 3, 
            'estimatedSecondsToCompletion': 0, 
            'kmsKeyId': 'AWS_OWNED_KMS_KEY', 
            'namespaceArn': 'arn:aws:redshift-serverless:us-west-2:111111111111:namespace/38d381f3-70d1-46ea-adf0-9debcdb04977', 
            'namespaceName': 'default-namespace', 
            'ownerAccount': '111111111111', 
            'snapshotArn': 'arn:aws:redshift-serverless:us-west-2:111111111111:snapshot/c497b35e-2a90-42e2-b221-f2cd303ff6aa',
            'snapshotName': 'test', 
            'snapshotRemainingDays': 0, 
            'snapshotRetentionPeriod': -1, 
            'snapshotRetentionStartTime': "", 
            'status': 'AVAILABLE', 
            'totalBackupSizeInMegaBytes': 786.0
            }
        ]
    
    mock_redshift_serverless(mocker,
               list_snapshots_response=list_snapshots_response,
               get_resource_policy_response=[])
    
    response = RedshiftServerlessPolicy(event=event).scan()
    logger.info(response)
    
    assert len(list(response)) == 2
    for resource in response:
        assert resource.get('PartitionKey') == PolicyType.RESOURCE_BASED_POLICY.value
    

def mock_redshift_serverless(mocker, list_snapshots_response=None, get_resource_policy_response=None):
    if list_snapshots_response is None:
        list_snapshots_response: list = []
    if get_resource_policy_response is None:
        get_resource_policy_response: str = ""
    
    def mock_list_snapshots(self):
        return list_snapshots_response
    
    mocker.patch(
        "aws.services.redshift_serverless.RedshiftServerless.list_snapshots",
        mock_list_snapshots
    )
    
    def mock_get_resource_policy(self, resource_arn: str):
        if resource_arn == "arn:aws:redshift-serverless:us-west-2:111111111111:snapshot/c497b35e-2a90-42e2-b221-f2cd303ff6aa":
            get_resource_policy_response = '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"AllowUserRestoreFromSnapshot\",\"Principal\":{\"AWS\":[\"111111111111\"]},\"Action\":[\"redshift-serverless:RestoreFromSnapshot\"],\
            \"Effect\":\"Allow\",\"Condition\":{\"StringEquals\":{\"aws:PrincipalOrgID\":\"o-eci09zojnh\"}},\"Resource\":\"arn:aws:redshift-serverless:us-west-2:111111111111:snapshot/c497b35e-2a90-42e2-b221-f2cd303ff6aa\"}]}'
        else:
            error_message = f"'There is no policy for resourceArn {resource_arn}. Create a resource-based policy and try your request again.'"
            get_resource_policy_response = {'Error':  error_message}
        return get_resource_policy_response
    
    mocker.patch(
        "aws.services.redshift_serverless.RedshiftServerless.get_resource_policy",
        mock_get_resource_policy
    )