# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

import resource_based_policy.step_functions_lambda.scan_policy_all_services as service
from assessment_runner.assessment_runner import write_task_failure
from resource_based_policy.resource_based_policies_repository import ResourceBasedPoliciesRepository
from resource_based_policy.resource_based_policy_model import ScanServiceRequestModel, ResourceBasedPolicyResponseModel
from resource_based_policy.supported_configuration.supported_regions_and_services import SUPPORTED_SERVICES

logger = Logger(getenv('LOG_LEVEL'))
tracer = Tracer()


@tracer.capture_lambda_handler
def lambda_handler(event: ScanServiceRequestModel, _context: LambdaContext):
    try:
        service_names = list(denormalize_service_names(service_data) for service_data in SUPPORTED_SERVICES)
        if event['ServiceName'] in service_names:
            method_name = f"scan_{event['ServiceName']}_policy"
            logger.debug("Resolving scan method for service " + event['ServiceName'])
            class_object = ScanPolicyStrategy(event)
            scan_method = getattr(
                class_object,
                method_name
            )
            policies = scan_method()
            if policies:
                ResourceBasedPoliciesRepository().create_all(policies)
        else:
            write_task_failure(
                event['JobId'],
                'RESOURCE_BASED_POLICY',
                event['AccountId'],
                None,
                event['ServiceName'],
                "Unsupported Service"
            )
    except ClientError as err:
        write_task_failure(
            event['JobId'],
            'RESOURCE_BASED_POLICY',
            event['AccountId'],
            None,
            event['ServiceName'],
            json.dumps(err.response)
        )


def denormalize_service_names(service_data):
    return service_data['ServiceName']


class ScanPolicyStrategy:
    def __init__(self, event: ScanServiceRequestModel):
        self.event = event
        self.logger = logger

    def scan_s3_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.S3BucketPolicy(self.event).scan()

    def scan_glacier_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.GlacierVaultPolicy(self.event).scan()

    def scan_iam_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.IAMPolicy(self.event).scan()

    def scan_sns_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.SNSTopicPolicy(self.event).scan()

    def scan_sqs_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.SQSQueuePolicy(self.event).scan()

    def scan_lambda_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.LambdaFunctionPolicy(self.event).scan()

    def scan_elasticfilesystem_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.ElasticFileSystemPolicy(self.event).scan()

    def scan_secretsmanager_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.SecretsManagerPolicy(self.event).scan()

    def scan_iot_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.IoTPolicy(self.event).scan()

    def scan_kms_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.KeyManagementServicePolicy(self.event).scan()

    def scan_apigateway_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.APIGatewayPolicy(self.event).scan()

    def scan_events_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.EventBusPolicy(self.event).scan()

    def scan_ses_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.SESIdentityPolicy(self.event).scan()

    def scan_ecr_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.EC2ContainerRegistryRepositoryPolicy(self.event).scan()

    def scan_config_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.ConfigRulePolicy(self.event).scan()

    def scan_ssm_incidents_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.SSMIncidentsResponsePlanPolicy(self.event).scan()

    def scan_opensearchservice_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.OpenSearchDomainPolicy(self.event).scan()

    def scan_cloudformation_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.CloudFormationStackPolicy(self.event).scan()

    def scan_glue_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.GlueResourcePolicy(self.event).scan()

    def scan_serverlessrepo_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.ServerlessApplicationPolicy(self.event).scan()

    def scan_backup_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.BackupVaultAccessPolicy(self.event).scan()

    def scan_codeartifact_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.CodeArtifactPolicy(self.event).scan()

    def scan_codebuild_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.CodeBuildResourcePolicy(self.event).scan()

    def scan_mediastore_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.MediaStorePolicy(self.event).scan()

    def scan_ec2_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return service.VPCEndpointsPolicy(self.event).scan()