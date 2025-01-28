#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
from os import getenv
from typing import Iterable

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

import policy_explorer.policy_explorer_model as model
from assessment_runner.assessment_runner import write_task_failure
from policy_explorer.policy_explorer_model import ScanServiceRequestModel, DynamoDBPolicyItem
from policy_explorer.policy_explorer_repository import PoliciesRepository
from policy_explorer.step_functions_lambda.scan_acm_pca_policy import ACMPCAPolicy
from policy_explorer.step_functions_lambda.scan_api_gateway_service_policy import APIGatewayPolicy
from policy_explorer.step_functions_lambda.scan_backup_vault_access_policy import BackupVaultAccessPolicy
from policy_explorer.step_functions_lambda.scan_cloudformation_stack_policy import CloudFormationStackPolicy
from policy_explorer.step_functions_lambda.scan_code_artifact_policy import CodeArtifactPolicy
from policy_explorer.step_functions_lambda.scan_code_build_resource_policy import CodeBuildResourcePolicy
from policy_explorer.step_functions_lambda.scan_config_rule_policy import ConfigRulePolicy
from policy_explorer.step_functions_lambda.scan_ec2_container_registry_repository_policy import \
    EC2ContainerRegistryRepositoryPolicy
from policy_explorer.step_functions_lambda.scan_elastic_file_system_policy import ElasticFileSystemPolicy
from policy_explorer.step_functions_lambda.scan_event_bus_policy import EventBusPolicy
from policy_explorer.step_functions_lambda.scan_eventbridge_schemas_policy import EventBridgeSchemasPolicy
from policy_explorer.step_functions_lambda.scan_glacier_vault_policy import GlacierVaultPolicy
from policy_explorer.step_functions_lambda.scan_glue_resource_policy import GlueResourcePolicy
from policy_explorer.step_functions_lambda.scan_iam_policy import IAMPolicy
from policy_explorer.step_functions_lambda.scan_iot_policy import IoTPolicy
from policy_explorer.step_functions_lambda.scan_key_management_service_policy import KeyManagementServicePolicy
from policy_explorer.step_functions_lambda.scan_lambda_function_policy import LambdaFunctionPolicy
from policy_explorer.step_functions_lambda.scan_lex_v2_models_policy import Lexv2ModelsPolicy
from policy_explorer.step_functions_lambda.scan_media_store_policy import MediaStorePolicy
from policy_explorer.step_functions_lambda.scan_open_search_domain_policy import OpenSearchDomainPolicy
from policy_explorer.step_functions_lambda.scan_organizations_policy import ServiceControlPolicy
from policy_explorer.step_functions_lambda.scan_ram_policy import RAMPolicy
from policy_explorer.step_functions_lambda.scan_redshift_serverless_policy import RedshiftServerlessPolicy
from policy_explorer.step_functions_lambda.scan_s3_bucket_policy import S3BucketPolicy
from policy_explorer.step_functions_lambda.scan_secrets_manager_policy import SecretsManagerPolicy
from policy_explorer.step_functions_lambda.scan_serverless_application_policy import ServerlessApplicationPolicy
from policy_explorer.step_functions_lambda.scan_ses_identity_policy import SESIdentityPolicy
from policy_explorer.step_functions_lambda.scan_sns_topic_policy import SNSTopicPolicy
from policy_explorer.step_functions_lambda.scan_sqs_queue_policies import SQSQueuePolicy
from policy_explorer.step_functions_lambda.scan_ssm_contacts_policy import SSMContactsPolicy
from policy_explorer.step_functions_lambda.scan_ssm_incidents_response_plan_policy import \
    SSMIncidentsResponsePlanPolicy
from policy_explorer.step_functions_lambda.scan_vpc_endpoints_policy import VPCEndpointsPolicy
from policy_explorer.supported_configuration.supported_regions_and_services import SUPPORTED_SERVICE_NAMES

logger = Logger(getenv('LOG_LEVEL'))
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: ScanServiceRequestModel, _context: LambdaContext):
    job_id = event.get('JobId')
    service_name = event['ServiceName']
    account_id = event['AccountId']

    if service_name not in SUPPORTED_SERVICE_NAMES:
        write_task_failure(
            job_id,
            'POLICY_EXPLORER',
            account_id,
            None,
            service_name,
            "Unsupported Service"
        )
        return

    try:
        scan_method = resolve_scan_method(event)
        if not scan_method:
            return
        policies: list[model.DynamoDBPolicyItem] = scan_method()
        for policy in policies:
            policy['JobId'] = job_id
        logger.info(f"Scanned policies for service {service_name}")
        if policies:
            logger.info('Saving {0} policies to DynamoDB'.format(str(len(policies))))
            PoliciesRepository().create_all(policies)
        else:
            logger.info('No policies for {0} in account {1}'.format(service_name, account_id))
    except ClientError as err:
        write_task_failure(
            job_id,
            'POLICY_EXPLORER',
            account_id,
            None,
            service_name,
            json.dumps(err.response)
        )
    except Exception as err:
        logger.exception("An unhandled error occurred", exc_info=True)
        write_task_failure(
            job_id,
            'POLICY_EXPLORER',
            account_id,
            None,
            service_name,
            repr(err)
        )


def resolve_scan_method(event):
    method_name = f"scan_{event['ServiceName']}_policy"
    logger.debug("Resolving scan method for service " + event['ServiceName'])
    class_object = ScanPolicyStrategy(event)
    try:
        scan_method = getattr(
            class_object,
            method_name
        )
        return scan_method
    except AttributeError as err:
        write_task_failure(
            event['JobId'],
            'POLICY_EXPLORER',
            event['AccountId'],
            None,
            event['ServiceName'],
            f"function {method_name} is not available in ScanPolicyStrategy."
        )
        return None


class ScanPolicyStrategy:
    def __init__(self, event: ScanServiceRequestModel):
        self.event = event
        self.logger = logger

    def scan_s3_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return S3BucketPolicy(self.event).scan()

    def scan_glacier_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return GlacierVaultPolicy(self.event).scan()

    def scan_iam_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return IAMPolicy(self.event).scan()

    def scan_sns_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return SNSTopicPolicy(self.event).scan()

    def scan_sqs_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return SQSQueuePolicy(self.event).scan()

    def scan_lambda_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return LambdaFunctionPolicy(self.event).scan()

    def scan_elasticfilesystem_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return ElasticFileSystemPolicy(self.event).scan()

    def scan_secretsmanager_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return SecretsManagerPolicy(self.event).scan()

    def scan_iot_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return IoTPolicy(self.event).scan()

    def scan_kms_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return KeyManagementServicePolicy(self.event).scan()

    def scan_apigateway_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return APIGatewayPolicy(self.event).scan()

    def scan_events_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return EventBusPolicy(self.event).scan()

    def scan_ses_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return SESIdentityPolicy(self.event).scan()

    def scan_ecr_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return EC2ContainerRegistryRepositoryPolicy(self.event).scan()

    def scan_config_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return ConfigRulePolicy(self.event).scan()

    def scan_ssm_incidents_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return SSMIncidentsResponsePlanPolicy(self.event).scan()

    def scan_opensearchservice_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return OpenSearchDomainPolicy(self.event).scan()

    def scan_cloudformation_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return CloudFormationStackPolicy(self.event).scan()

    def scan_glue_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return GlueResourcePolicy(self.event).scan()

    def scan_serverlessrepo_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return ServerlessApplicationPolicy(self.event).scan()

    def scan_backup_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return BackupVaultAccessPolicy(self.event).scan()

    def scan_codeartifact_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return CodeArtifactPolicy(self.event).scan()

    def scan_codebuild_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return CodeBuildResourcePolicy(self.event).scan()

    def scan_mediastore_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return MediaStorePolicy(self.event).scan()

    def scan_ec2_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return VPCEndpointsPolicy(self.event).scan()

    def scan_lexv2_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return Lexv2ModelsPolicy(self.event).scan()

    def scan_redshift_serverless_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return RedshiftServerlessPolicy(self.event).scan()

    def scan_acm_pca_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return ACMPCAPolicy(self.event).scan()

    def scan_ssm_contacts_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return SSMContactsPolicy(self.event).scan()

    def scan_eventbridge_schemas_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return EventBridgeSchemasPolicy(self.event).scan()

    def scan_ram_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return RAMPolicy(self.event).scan()

    def scan_organizations_policy(self) -> Iterable[DynamoDBPolicyItem]:
        return ServiceControlPolicy(self.event).scan()
