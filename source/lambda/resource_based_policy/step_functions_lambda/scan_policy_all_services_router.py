# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

from assessment_runner.assessment_runner import write_task_failure
from resource_based_policy.resource_based_policies_repository import ResourceBasedPoliciesRepository
from resource_based_policy.resource_based_policy_model import ScanServiceRequestModel, ResourceBasedPolicyResponseModel
from resource_based_policy.step_functions_lambda.scan_api_gateway_service_policy import APIGatewayPolicy
from resource_based_policy.step_functions_lambda.scan_backup_vault_access_policy import BackupVaultAccessPolicy
from resource_based_policy.step_functions_lambda.scan_cloudformation_stack_policy import CloudFormationStackPolicy
from resource_based_policy.step_functions_lambda.scan_code_artifact_policy import CodeArtifactPolicy
from resource_based_policy.step_functions_lambda.scan_code_build_resource_policy import CodeBuildResourcePolicy
from resource_based_policy.step_functions_lambda.scan_config_rule_policy import ConfigRulePolicy
from resource_based_policy.step_functions_lambda.scan_ec2_container_registry_repository_policy import \
    EC2ContainerRegistryRepositoryPolicy
from resource_based_policy.step_functions_lambda.scan_elastic_file_system_policy import ElasticFileSystemPolicy
from resource_based_policy.step_functions_lambda.scan_event_bus_policy import EventBusPolicy
from resource_based_policy.step_functions_lambda.scan_glacier_vault_policy import GlacierVaultPolicy
from resource_based_policy.step_functions_lambda.scan_glue_resource_policy import GlueResourcePolicy
from resource_based_policy.step_functions_lambda.scan_iam_policy import IAMPolicy
from resource_based_policy.step_functions_lambda.scan_iot_policy import IoTPolicy
from resource_based_policy.step_functions_lambda.scan_key_management_service_policy import KeyManagementServicePolicy
from resource_based_policy.step_functions_lambda.scan_lambda_function_policy import LambdaFunctionPolicy
from resource_based_policy.step_functions_lambda.scan_media_store_policy import MediaStorePolicy
from resource_based_policy.step_functions_lambda.scan_open_search_domain_policy import OpenSearchDomainPolicy
from resource_based_policy.step_functions_lambda.scan_s3_bucket_policy import S3BucketPolicy
from resource_based_policy.step_functions_lambda.scan_secrets_manager_policy import SecretsManagerPolicy
from resource_based_policy.step_functions_lambda.scan_serverless_application_policy import ServerlessApplicationPolicy
from resource_based_policy.step_functions_lambda.scan_ses_identity_policy import SESIdentityPolicy
from resource_based_policy.step_functions_lambda.scan_sns_topic_policy import SNSTopicPolicy
from resource_based_policy.step_functions_lambda.scan_sqs_queue_policies import SQSQueuePolicy
from resource_based_policy.step_functions_lambda.scan_ssm_incidents_response_plan_policy import \
    SSMIncidentsResponsePlanPolicy
from resource_based_policy.step_functions_lambda.scan_vpc_endpoints_policy import VPCEndpointsPolicy
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
        return S3BucketPolicy(self.event).scan()

    def scan_glacier_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return GlacierVaultPolicy(self.event).scan()

    def scan_iam_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return IAMPolicy(self.event).scan()

    def scan_sns_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return SNSTopicPolicy(self.event).scan()

    def scan_sqs_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return SQSQueuePolicy(self.event).scan()

    def scan_lambda_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return LambdaFunctionPolicy(self.event).scan()

    def scan_elasticfilesystem_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return ElasticFileSystemPolicy(self.event).scan()

    def scan_secretsmanager_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return SecretsManagerPolicy(self.event).scan()

    def scan_iot_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return IoTPolicy(self.event).scan()

    def scan_kms_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return KeyManagementServicePolicy(self.event).scan()

    def scan_apigateway_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return APIGatewayPolicy(self.event).scan()

    def scan_events_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return EventBusPolicy(self.event).scan()

    def scan_ses_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return SESIdentityPolicy(self.event).scan()

    def scan_ecr_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return EC2ContainerRegistryRepositoryPolicy(self.event).scan()

    def scan_config_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return ConfigRulePolicy(self.event).scan()

    def scan_ssm_incidents_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return SSMIncidentsResponsePlanPolicy(self.event).scan()

    def scan_opensearchservice_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return OpenSearchDomainPolicy(self.event).scan()

    def scan_cloudformation_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return CloudFormationStackPolicy(self.event).scan()

    def scan_glue_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return GlueResourcePolicy(self.event).scan()

    def scan_serverlessrepo_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return ServerlessApplicationPolicy(self.event).scan()

    def scan_backup_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return BackupVaultAccessPolicy(self.event).scan()

    def scan_codeartifact_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return CodeArtifactPolicy(self.event).scan()

    def scan_codebuild_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return CodeBuildResourcePolicy(self.event).scan()

    def scan_mediastore_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return MediaStorePolicy(self.event).scan()

    def scan_ec2_policy(self) -> Iterable[ResourceBasedPolicyResponseModel]:
        return VPCEndpointsPolicy(self.event).scan()
