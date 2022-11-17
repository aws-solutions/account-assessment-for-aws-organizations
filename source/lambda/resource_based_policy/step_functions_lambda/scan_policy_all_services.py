# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from datetime import datetime
from os import getenv
from typing import Iterable, Callable
from aws_lambda_powertools import Logger
from mypy_boto3_apigateway.type_defs import RestApiResponseMetadataTypeDef
from mypy_boto3_backup.type_defs import BackupVaultListMemberTypeDef, GetBackupVaultAccessPolicyOutputTypeDef
from mypy_boto3_cloudformation.type_defs import StackSummaryTypeDef, GetStackPolicyOutputTypeDef
from mypy_boto3_codeartifact.type_defs import DomainSummaryTypeDef, GetDomainPermissionsPolicyResultTypeDef, \
    RepositorySummaryTypeDef, GetRepositoryPermissionsPolicyResultTypeDef
from mypy_boto3_codebuild.type_defs import ProjectTypeDef, GetResourcePolicyOutputTypeDef
from mypy_boto3_config.type_defs import OrganizationConfigRuleTypeDef, GetCustomRulePolicyResponseTypeDef
from mypy_boto3_ec2.type_defs import VpcEndpointTypeDef
from mypy_boto3_ecr.type_defs import GetRepositoryPolicyResponseTypeDef, RepositoryTypeDef
from mypy_boto3_efs.type_defs import FileSystemDescriptionTypeDef
from mypy_boto3_events.type_defs import EventBusTypeDef
from mypy_boto3_glacier.type_defs import DescribeVaultOutputTypeDef, VaultAccessPolicyTypeDef
from mypy_boto3_glue.type_defs import GluePolicyTypeDef
from mypy_boto3_iam.type_defs import PolicyTypeDef as IAMPolicyTypeDef, PolicyVersionTypeDef, RoleTypeDef
from mypy_boto3_iot.type_defs import PolicyTypeDef as IotPolicyTypeDef, GetPolicyResponseTypeDef as \
    IoTGetPolicyResponseTypeDef
from mypy_boto3_kms.type_defs import KeyListEntryTypeDef, GetKeyPolicyResponseTypeDef
from mypy_boto3_lambda.type_defs import FunctionConfigurationTypeDef, GetPolicyResponseTypeDef
from mypy_boto3_mediastore.type_defs import ContainerTypeDef, GetContainerPolicyOutputTypeDef
from mypy_boto3_opensearch.type_defs import DomainInfoTypeDef, DomainStatusTypeDef
from mypy_boto3_s3.type_defs import BucketTypeDef, GetBucketPolicyOutputTypeDef
from mypy_boto3_secretsmanager.type_defs import GetResourcePolicyResponseTypeDef, SecretListEntryTypeDef
from mypy_boto3_serverlessrepo.type_defs import ApplicationSummaryTypeDef, ApplicationPolicyStatementTypeDef
from mypy_boto3_sesv2.type_defs import IdentityInfoTypeDef
from mypy_boto3_sns.type_defs import TopicTypeDef, GetTopicAttributesResponseTypeDef
from mypy_boto3_sqs.type_defs import GetQueueAttributesResultTypeDef
from mypy_boto3_ssm_incidents.type_defs import ResourcePolicyTypeDef, ResponsePlanSummaryTypeDef

import resource_based_policy.resource_based_policy_model as model
from assessment_runner.assessment_runner import write_task_failure
from aws.services.api_gateway import APIGateway
from aws.services.backup import Backup
from aws.services.cloud_formation import CloudFormation
from aws.services.code_artifact import CodeArtifact
from aws.services.code_build import CodeBuild
from aws.services.config import Config
from aws.services.ec2 import EC2
from aws.services.ec2_container_registry import EC2ContainerRegistry
from aws.services.elastic_file_system import ElasticFileSystem
from aws.services.events import Events
from aws.services.glue import Glue
from aws.services.iam import IAM
from aws.services.iot import IoT
from aws.services.key_management_service import KeyManagementService
from aws.services.lambda_functions import LambdaFunctions
from aws.services.media_store import MediaStore
from aws.services.open_search import OpenSearch
from aws.services.s3 import S3, Glacier
from aws.services.secrets_manager import SecretsManager
from aws.services.serverless_application_repository import ServerlessApplicationRepository
from aws.services.simple_email_service_v2 import SimpleEmailServiceV2
from aws.services.sns import SNS
from aws.services.sqs import SQS
from aws.services.ssm_incidents import SSMIncidents
from aws.utils.exceptions import ServiceUnavailable, RegionNotEnabled, ConnectionTimeout, \
    AccountAssessmentClientException, AccessDenied
from resource_based_policy.step_functions_lambda.check_policy_for_organizations_dependency import \
    CheckForOrganizationsDependency, CheckServerlessAppRepoForOrganizationsDependency
from utils.string_manipulation import trim_string_split_to_list_get_last_item as get_name_from_arn, \
    trim_string_from_front


def scan_regions(event: model.ScanServiceRequestModel,
                 scan_single_region: Callable[[str], Iterable[model.ResourceBasedPolicyResponseModel]]) -> \
        list[model.ResourceBasedPolicyResponseModel]:
    logger = Logger(service='scan_regions', level=getenv('LOG_LEVEL'))
    resources_in_all_regions = []
    for region in event['Regions']:
        try:
            resources_for_region = scan_single_region(region)
            resources_in_all_regions.extend(resources_for_region)
        except (ServiceUnavailable, RegionNotEnabled, ConnectionTimeout,
                AccountAssessmentClientException, AccessDenied) as err:
            logger.debug(f"[{event['AccountId']}][{event['ServiceName']}] Handling Error: {err.message}. Writing "
                         f"failed task to JobHistory DynamoDB Table")
            write_task_failure(
                event['JobId'],
                'RESOURCE_BASED_POLICY',
                event['AccountId'],
                region,
                event['ServiceName'],
                json.dumps(err.message) if hasattr(err, 'message') else json.dumps(err)
            )
    return resources_in_all_regions


class S3BucketPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.s3_client = S3(event['AccountId'])

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        bucket_names = self._get_bucket_names()
        bucket_names_policies = self._get_bucket_policies(bucket_names)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(bucket_names_policies)
        return list(DenormalizeResourceBasedPolicyResponse(self.event).model(resource) for resource in
                    resources_dependent_on_organizations)

    def _get_bucket_names(self) -> list[str]:
        bucket_objects: list[BucketTypeDef] = self.s3_client.list_buckets().get('Buckets', [])
        return [bucket.get('Name') for bucket in bucket_objects]

    def _get_bucket_policies(self, bucket_names) -> list[model.PolicyAnalyzerRequest]:
        bucket_names_policies = []
        for bucket in bucket_names:
            policy: GetBucketPolicyOutputTypeDef = self.s3_client.get_bucket_policy(bucket)
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    bucket,
                    policy.get('Policy')
                )
                bucket_names_policies.append(policy_object)
        return bucket_names_policies


class GlacierVaultPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.glacier_client = Glacier(event['AccountId'])

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        vault_names = self._get_vault_names()
        vault_names_policies = self._get_vault_policies(vault_names)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(vault_names_policies)
        return list(DenormalizeResourceBasedPolicyResponse(self.event).model(resource) for resource in
                    resources_dependent_on_organizations)

    def _get_vault_names(self) -> list[str]:
        vault_name: list[DescribeVaultOutputTypeDef] = self.glacier_client.list_vaults()
        return [vault.get('VaultName') for vault in vault_name]

    def _get_vault_policies(self, vault_names) -> list[model.PolicyAnalyzerRequest]:
        vault_names_policies = []
        for vault in vault_names:
            policy: VaultAccessPolicyTypeDef = self.glacier_client.get_vault_access_policy(vault)
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    vault,
                    policy.get('Policy')
                )
                vault_names_policies.append(policy_object)
        return vault_names_policies


class IAMPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.iam_client = IAM(event['AccountId'])

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        iam_policies_with_org_dependency = self.scan_iam_policy()
        assumed_role_policy_with_org_dependency = self.scan_assume_role_policy()
        iam_resources_with_org_dependency = [
            *iam_policies_with_org_dependency,
            *assumed_role_policy_with_org_dependency
        ]
        return iam_resources_with_org_dependency

    def scan_iam_policy(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        policy_data: list[model.IAMPolicyData] = self._get_policy_data()
        policy_names_documents = self._get_iam_policy_names_and_documents(policy_data)
        iam_policies_with_org_condition: list[model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(
            policy_names_documents)
        return list(DenormalizeResourceBasedPolicyResponse(self.event).model(resource) for resource in
                    iam_policies_with_org_condition)

    def _get_policy_data(self) -> list[model.IAMPolicyData]:
        iam_policy_objects: list[IAMPolicyTypeDef] = self.iam_client.list_policies()
        return list(self.denormalize_to_iam_policy_data(policy) for policy in iam_policy_objects)

    @staticmethod
    def denormalize_to_iam_policy_data(policy: IAMPolicyTypeDef) -> model.IAMPolicyData:
        data: model.IAMPolicyData = {
            "Arn": policy['Arn'],
            "DefaultVersionId": policy['DefaultVersionId'],
            "PolicyName": policy['PolicyName']
        }
        return data

    def _get_iam_policy_names_and_documents(
            self, policy_data: list[model.IAMPolicyData]) -> list[model.PolicyAnalyzerRequest]:
        iam_policies = []
        for policy in policy_data:
            policy_document: PolicyVersionTypeDef = self.iam_client.get_policy_version(
                policy.get('Arn'),
                policy.get('DefaultVersionId')
            )
            if policy_document.get('Document'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    f"{policy['PolicyName']}#IAMPolicy",  # IAM Role and Policy can have same name
                    policy_document['Document']
                )
                iam_policies.append(policy_object)
        return iam_policies

    def scan_assume_role_policy(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        role_names_assume_role_policy_documents = self._get_role_names_and_assume_role_policy_documents()
        iam_policies_with_org_condition: list[model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(
            role_names_assume_role_policy_documents)
        return list(DenormalizeResourceBasedPolicyResponse(self.event).model(resource) for resource in
                    iam_policies_with_org_condition)

    def _get_role_names_and_assume_role_policy_documents(self) -> list[model.PolicyAnalyzerRequest]:
        roles: list[RoleTypeDef] = self.iam_client.list_roles()
        role_names_assume_role_policies = []
        for role in roles:
            if role.get('AssumeRolePolicyDocument'):
                role_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    f"{role['RoleName']}#IAMRole",  # IAM Role and Policy can have same name
                    role['AssumeRolePolicyDocument']
                )
                role_names_assume_role_policies.append(role_object)
        return role_names_assume_role_policies


class SNSTopicPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning SNS Topic Policies in {region}")
        sns_client = SNS(self.account_id, region)
        topic_arns: list[TopicTypeDef] = sns_client.list_topics()
        topic_names_and_policies = self._get_topic_names_and_policies(topic_arns, sns_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(topic_names_and_policies)
        sns_resources_for_region = list(
            DenormalizeResourceBasedPolicyResponse(self.event).model(resource, region) for resource in
            resources_dependent_on_organizations)
        return sns_resources_for_region

    def _get_topic_names_and_policies(
            self, topic_arns: list[TopicTypeDef], sns_client) -> list[model.PolicyAnalyzerRequest]:
        topic_names_and_policies = list(
            self._get_topic_policy(topic_arn['TopicArn'], sns_client) for topic_arn in topic_arns)
        self.logger.info(topic_names_and_policies)
        return topic_names_and_policies

    @staticmethod
    def _get_topic_policy(topic_arn: str, sns_client) -> model.PolicyAnalyzerRequest:
        topic_attributes: GetTopicAttributesResponseTypeDef = sns_client.get_topic_attributes(topic_arn)
        if topic_attributes.get('Attributes').get('Policy'):
            topic_name = get_name_from_arn(topic_attributes.get('Attributes').get('TopicArn'))
            policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                topic_name,
                topic_attributes.get('Attributes').get('Policy')
            )
            return policy_object


class SQSQueuePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning SQS Queue Policies in {region}")
        sqs_client = SQS(self.account_id, region)
        queue_urls = sqs_client.list_queues()
        queue_names_and_policies = self._get_queue_urls_and_policies(queue_urls, sqs_client)
        self.logger.info(queue_names_and_policies)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(queue_names_and_policies)
        sqs_resources_for_region = list(
            DenormalizeResourceBasedPolicyResponse(self.event).model(resource, region) for resource in
            resources_dependent_on_organizations)
        return sqs_resources_for_region

    def _get_queue_urls_and_policies(self, queue_urls: list[str], sqs_client) -> list[model.PolicyAnalyzerRequest]:
        return list(self._get_queue_policy(queue_url, sqs_client) for queue_url in queue_urls)

    @staticmethod
    def _get_queue_policy(queue_url: str, sqs_client) -> model.PolicyAnalyzerRequest:
        attribute_names = ['QueueArn', 'Policy']
        queue_attributes: GetQueueAttributesResultTypeDef = sqs_client.get_queue_attributes(
            queue_url,
            attribute_names
        )
        if queue_attributes.get('Attributes').get('Policy'):
            queue_name = get_name_from_arn(queue_attributes.get('Attributes').get('QueueArn'))
            policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                queue_name,
                queue_attributes.get('Attributes').get('Policy')
            )
            return policy_object


class LambdaFunctionPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Lambda Function Policies in {region}")
        lambda_client = LambdaFunctions(self.account_id, region)
        lambda_function_data: list[model.LambdaFunctionData] = self._get_lambda_function_data(lambda_client)
        lambda_function_names_policies = self._get_lambda_function_policy(lambda_function_data, lambda_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(lambda_function_names_policies)
        lambda_function_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
                resource, region) for resource in resources_dependent_on_organizations)
        return lambda_function_resources_for_region

    def _get_lambda_function_data(self, lambda_client) -> list[model.LambdaFunctionData]:
        lambda_function_objects: list[FunctionConfigurationTypeDef] = lambda_client.list_functions()
        return list(self.denormalize_to_lambda_function_data(function_data) for function_data in
                    lambda_function_objects)

    @staticmethod
    def denormalize_to_lambda_function_data(function_data: FunctionConfigurationTypeDef) -> model.LambdaFunctionData:
        lambda_function_data: model.LambdaFunctionData = {
            "FunctionName": function_data['FunctionName']
        }
        return lambda_function_data

    @staticmethod
    def _get_lambda_function_policy(lambda_function_data: list[model.LambdaFunctionData],
                                    lambda_client) -> list[model.PolicyAnalyzerRequest]:
        lambda_policies = []
        for lambda_function in lambda_function_data:
            policy: GetPolicyResponseTypeDef = lambda_client.get_policy(
                lambda_function.get('FunctionName')
            )
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    lambda_function.get('FunctionName'),
                    policy.get('Policy')
                )
                lambda_policies.append(policy_object)
        return lambda_policies


class ElasticFileSystemPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning File System Policies in {region}")
        efs_client = ElasticFileSystem(self.account_id, region)
        file_system_id: list[model.EFSData] = self._get_file_system_id(efs_client)
        efs_names_policies = self._get_efs_policy(file_system_id, efs_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(efs_names_policies)
        efs_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return efs_resources_for_region

    def _get_file_system_id(self, efs_client) -> list[model.EFSData]:
        file_system_description: list[FileSystemDescriptionTypeDef] = efs_client.describe_file_systems()
        return list(self.denormalize_to_file_system_id(file_system_id) for file_system_id in
                    file_system_description)

    @staticmethod
    def denormalize_to_file_system_id(file_system_id: FileSystemDescriptionTypeDef) -> model.EFSData:
        data: model.EFSData = {
            "FileSystemId": file_system_id['FileSystemId']
        }
        return data

    @staticmethod
    def _get_efs_policy(file_system_id: list[model.EFSData], efs_client) -> list[model.PolicyAnalyzerRequest]:
        efs_policies = []
        for efs in file_system_id:
            policy: model.DescribeFileSystemPolicyResponse = efs_client.describe_file_system_policy(
                efs.get('FileSystemId')
            )
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    policy['FileSystemId'],
                    policy['Policy']
                )
                efs_policies.append(policy_object)
        return efs_policies


class SecretsManagerPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Policies attached to the Secrets in {region}")
        secrets_manager_client = SecretsManager(self.account_id, region)
        secrets_manager_data: list[model.SecretsManagerData] = self._get_secrets_manager_data(
            secrets_manager_client)
        secrets_manager_names_policies = self._get_secrets_manager_policy(secrets_manager_data,
                                                                          secrets_manager_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(secrets_manager_names_policies)
        secrets_manager_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
                resource, region) for resource in resources_dependent_on_organizations)
        return secrets_manager_resources_for_region

    def _get_secrets_manager_data(self, secrets_manager_client) -> list[model.SecretsManagerData]:
        secrets_manager_objects: list[SecretListEntryTypeDef] = secrets_manager_client.list_secrets()
        return list(self.denormalize_to_secrets_manager_data(secrets_manager_data) for secrets_manager_data in
                    secrets_manager_objects)

    @staticmethod
    def denormalize_to_secrets_manager_data(secrets_manager_data: SecretListEntryTypeDef) -> model.SecretsManagerData:
        data: model.SecretsManagerData = {
            "Name": secrets_manager_data['Name']
        }
        return data

    @staticmethod
    def _get_secrets_manager_policy(secrets_manager_data: list[model.SecretsManagerData],
                                    secrets_manager_client) -> list[model.PolicyAnalyzerRequest]:
        secrets_manager_policies = []
        for secrets_manager in secrets_manager_data:
            policy: GetResourcePolicyResponseTypeDef = secrets_manager_client.get_resource_policy(
                secrets_manager.get('Name')
            )
            if policy.get('ResourcePolicy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    secrets_manager.get('Name'),
                    policy['ResourcePolicy']
                )
                secrets_manager_policies.append(policy_object)
        return secrets_manager_policies


class IoTPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning IoT Policies in {region}")
        iot_client = IoT(self.account_id, region)
        iot_data: list[model.IoTData] = self._get_iot_data(iot_client)
        iot_names_policies = self._get_iot_policy(iot_data, iot_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(iot_names_policies)
        iot_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return iot_resources_for_region

    def _get_iot_data(self, iot_client) -> list[model.IoTData]:
        iot_objects: list[IotPolicyTypeDef] = iot_client.list_policies()
        return list(self.denormalize_to_iot_data(iot_data) for iot_data in iot_objects)

    @staticmethod
    def denormalize_to_iot_data(iot_data: IotPolicyTypeDef) -> model.IoTData:
        data: model.IoTData = {
            "policyName": iot_data['policyName']
        }
        return data

    @staticmethod
    def _get_iot_policy(iot_data: list[model.IoTData], iot_client) -> list[model.PolicyAnalyzerRequest]:
        iot_policies = []
        for iot in iot_data:
            policy: IoTGetPolicyResponseTypeDef = iot_client.get_policy(
                iot.get('policyName')
            )
            if policy.get('policyDocument'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    iot.get('policyName'),
                    policy['policyDocument']
                )
                iot_policies.append(policy_object)
        return iot_policies


class KeyManagementServicePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning KMS Key Policies in {region}")
        kms_client = KeyManagementService(self.account_id, region)
        kms_keys: list[model.KMSData] = self._get_kms_keys(kms_client)
        kms_names_policies = self._get_kms_policy(kms_keys, kms_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(kms_names_policies)
        kms_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return kms_resources_for_region

    def _get_kms_keys(self, kms_client) -> list[model.KMSData]:
        kms_objects: list[KeyListEntryTypeDef] = kms_client.list_keys()
        return list(self.denormalize_to_kms_keys(kms_keys) for kms_keys in kms_objects)

    @staticmethod
    def denormalize_to_kms_keys(kms_keys: KeyListEntryTypeDef) -> model.KMSData:
        data: model.KMSData = {
            "KeyId": kms_keys['KeyId']
        }
        return data

    @staticmethod
    def _get_kms_policy(kms_keys: list[model.KMSData], kms_client) -> list[model.PolicyAnalyzerRequest]:
        kms_policies = []
        for key in kms_keys:
            policy: GetKeyPolicyResponseTypeDef = kms_client.get_key_policy(
                key.get('KeyId')
            )
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    key.get('KeyId'),
                    policy['Policy']
                )
                kms_policies.append(policy_object)
        return kms_policies


class APIGatewayPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning API Gateway Policies in {region}")
        apigateway_client = APIGateway(self.account_id, region)
        apigateway_names_policies: list[model.PolicyAnalyzerRequest] = self._get_apigateway_names_policies(
            apigateway_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(apigateway_names_policies)
        apigateway_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return apigateway_resources_for_region

    def _get_apigateway_names_policies(self, apigateway_client) -> list[model.PolicyAnalyzerRequest]:
        apigateway_objects: list[RestApiResponseMetadataTypeDef] = apigateway_client.get_rest_apis()
        return list(self.denormalize_to_apigateway_data(apigateway_data) for apigateway_data in apigateway_objects)

    @staticmethod
    def denormalize_to_apigateway_data(apigateway_data: RestApiResponseMetadataTypeDef) -> model.PolicyAnalyzerRequest:
        if apigateway_data.get('policy'):
            return DenormalizePolicyAnalyzerRequest().model(
                apigateway_data['name'],
                apigateway_data['policy']
            )


class EventBusPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Event Bus Policies in {region}")
        events_client = Events(self.account_id, region)
        events_names_policies: list[model.PolicyAnalyzerRequest] = self._get_events_data(events_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(events_names_policies)
        events_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return events_resources_for_region

    def _get_events_data(self, events_client) -> list[model.PolicyAnalyzerRequest]:
        events_objects: list[EventBusTypeDef] = events_client.list_event_buses()
        return list(self.denormalize_to_events_data(events_data) for events_data in events_objects)

    @staticmethod
    def denormalize_to_events_data(events_data: EventBusTypeDef) -> model.PolicyAnalyzerRequest:
        if events_data.get('Policy'):
            return DenormalizePolicyAnalyzerRequest().model(
                events_data['Name'],
                events_data['Policy']
            )


class SESIdentityPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning SES Identity Policies in {region}")
        ses_client = SimpleEmailServiceV2(self.account_id, region)
        ses_identity_data: list[IdentityInfoTypeDef] = ses_client.list_email_identities()
        ses_identities_policies = self._get_ses_policies(ses_identity_data, ses_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(ses_identities_policies)
        ses_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return ses_resources_for_region

    @staticmethod
    def _get_ses_policies(ses_data: list[IdentityInfoTypeDef], ses_client) -> list[model.PolicyAnalyzerRequest]:
        ses_policies = []
        for ses in ses_data:
            policies: dict[str, str] = ses_client.get_email_identity_policies(
                ses['IdentityName']
            ).get('Policies')

            # create a map for each policy per identity
            for policy_name, policy in policies.items():
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    f"{ses['IdentityName']}_{policy_name}",
                    policy
                )
                ses_policies.append(policy_object)
        return ses_policies


class EC2ContainerRegistryRepositoryPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning ECR Repository Policies in {region}")
        ecr_client = EC2ContainerRegistry(self.account_id, region)
        ecr_data: list[model.ECRData] = self._get_ecr_data(ecr_client)
        ecr_repo_policies = self._get_ecr_policies(ecr_data, ecr_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(ecr_repo_policies)
        ecr_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return ecr_resources_for_region

    def _get_ecr_data(self, ecr_client) -> list[model.ECRData]:
        ecr_objects: list[RepositoryTypeDef] = ecr_client.describe_repositories()
        return list(self.denormalize_to_ecr_data(ecr_data) for ecr_data in ecr_objects)

    @staticmethod
    def denormalize_to_ecr_data(ecr_data: RepositoryTypeDef) -> model.ECRData:
        data: model.ECRData = {
            "repositoryName": ecr_data['repositoryName']
        }
        return data

    @staticmethod
    def _get_ecr_policies(ecr_data: list[model.ECRData], ecr_client) -> list[model.PolicyAnalyzerRequest]:
        ecr_policies = []
        for ecr in ecr_data:
            policy: GetRepositoryPolicyResponseTypeDef = ecr_client.get_repository_policy(
                ecr['repositoryName']
            )
            if policy.get('policyText'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    policy['repositoryName'],
                    policy['policyText']
                )
                ecr_policies.append(policy_object)
        return ecr_policies


class ConfigRulePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Config Rule Policies in {region}")
        config_client = Config(self.account_id, region)
        config_rules: list[model.ConfigData] = self._get_config_rules(config_client)
        config_rule_policies = self._get_config_rule_policies(config_rules, config_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(config_rule_policies)
        config_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return config_resources_for_region

    def _get_config_rules(self, config_client) -> list[model.ConfigData]:
        config_objects: list[OrganizationConfigRuleTypeDef] = config_client.describe_organization_config_rules()
        return list(self.denormalize_to_config_data(config_data) for config_data in config_objects)

    @staticmethod
    def denormalize_to_config_data(config_data: OrganizationConfigRuleTypeDef) -> model.ConfigData:
        data: model.ConfigData = {
            "OrganizationConfigRuleName": config_data['OrganizationConfigRuleName']
        }
        return data

    @staticmethod
    def _get_config_rule_policies(
            config_data: list[model.ConfigData], config_client) -> list[model.PolicyAnalyzerRequest]:
        config_policies = []
        for config in config_data:
            policy: GetCustomRulePolicyResponseTypeDef = config_client.get_organization_custom_rule_policy(
                config['OrganizationConfigRuleName']
            )
            if policy.get('PolicyText'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    config['OrganizationConfigRuleName'],
                    policy['PolicyText']
                )
                config_policies.append(policy_object)
        return config_policies


class SSMIncidentsResponsePlanPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning SSM Incident Response Plan Policies in {region}")
        ssm_incidents_client = SSMIncidents(self.account_id, region)
        ssm_incidents_data: list[model.SSMIncidentsData] = self._get_response_plan_data(ssm_incidents_client)
        ssm_incidents_resource_policies = self._get_ssm_incidents_policies(ssm_incidents_data, ssm_incidents_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(ssm_incidents_resource_policies)
        ssm_incidents_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return ssm_incidents_resources_for_region

    def _get_response_plan_data(self, ssm_incidents_client) -> list[model.SSMIncidentsData]:
        ssm_incidents_objects: list[ResponsePlanSummaryTypeDef] = ssm_incidents_client.list_response_plans()
        return list(self.denormalize_to_ssm_incidents_data(ssm_incidents_data) for ssm_incidents_data in
                    ssm_incidents_objects)

    @staticmethod
    def denormalize_to_ssm_incidents_data(ssm_incidents_data: ResponsePlanSummaryTypeDef) -> model.SSMIncidentsData:
        data: model.SSMIncidentsData = {
            "arn": ssm_incidents_data['arn'],
            "name": ssm_incidents_data['name']
        }
        return data

    @staticmethod
    def _get_ssm_incidents_policies(
            ssm_incidents_data: list[model.SSMIncidentsData],
            ssm_incidents_client) -> list[model.PolicyAnalyzerRequest]:
        ssm_incidents_policies = []
        for response_plan in ssm_incidents_data:
            policies: list[ResourcePolicyTypeDef] = ssm_incidents_client.get_resource_policies(
                response_plan['arn']
            )
            for policy in policies:
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    f"{response_plan['name']}_{policy['policyId']}",
                    policy['policyDocument']
                )
                ssm_incidents_policies.append(policy_object)
        return ssm_incidents_policies


class OpenSearchDomainPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning OpenSearch Domain Policies in {region}")
        opensearch_client = OpenSearch(self.account_id, region)
        opensearch_domain_names: model.OpenSearchData = self._get_opensearch_domain_names(opensearch_client)
        opensearch_domain_policies = self._get_opensearch_domain_policies(opensearch_domain_names,
                                                                          opensearch_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(opensearch_domain_policies)
        opensearch_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return opensearch_resources_for_region

    def _get_opensearch_domain_names(self, opensearch_client) -> model.OpenSearchData:
        domain_objects: list[DomainInfoTypeDef] = opensearch_client.list_domain_names()
        return self.denormalize_to_opensearch_data(domain_objects)

    @staticmethod
    def denormalize_to_opensearch_data(domain_data: list[DomainInfoTypeDef]) -> model.OpenSearchData:
        domain_names = []
        for domain in domain_data:
            domain_names.append(domain['DomainName'])
        data: model.OpenSearchData = {
            "DomainNames": domain_names
        }
        return data

    @staticmethod
    def _get_opensearch_domain_policies(
            opensearch_data: model.OpenSearchData,
            opensearch_client) -> list[model.PolicyAnalyzerRequest]:
        opensearch_policies = []
        if opensearch_data.get('DomainNames'):
            domain_policies: list[DomainStatusTypeDef] = opensearch_client.describe_domains(
                opensearch_data['DomainNames']
            )
            for policy in domain_policies:
                if policy.get('AccessPolicies'):
                    policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                        policy['DomainName'],
                        policy['AccessPolicies']
                    )
                    opensearch_policies.append(policy_object)
        return opensearch_policies


class CloudFormationStackPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Cloud Formation Stack Policies in {region}")
        cloudformation_client = CloudFormation(self.account_id, region)
        stack_summaries: list[StackSummaryTypeDef] = cloudformation_client.list_stacks()
        stack_names_and_policies = self._get_stack_names_and_policies(stack_summaries, cloudformation_client)
        self.logger.info(stack_names_and_policies)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(stack_names_and_policies)
        cloudformation_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
                resource, region) for resource in resources_dependent_on_organizations)
        return cloudformation_resources_for_region

    def _get_stack_names_and_policies(
            self, stack_summaries: list[StackSummaryTypeDef],
            cloudformation_client) -> list[model.PolicyAnalyzerRequest]:
        return list(self._get_stack_policies(summary['StackName'], cloudformation_client) for summary in
                    stack_summaries)

    @staticmethod
    def _get_stack_policies(stack_name: str, cloudformation_client) -> model.PolicyAnalyzerRequest:
        stack_policy: GetStackPolicyOutputTypeDef = cloudformation_client.get_stack_policy(stack_name)
        if stack_policy.get('StackPolicyBody'):
            policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                stack_name,
                stack_policy['StackPolicyBody']
            )
            return policy_object


class GlueResourcePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Glue Resource Policies in {region}")
        glue_client = Glue(self.account_id, region)
        glue_names_policies: list[model.PolicyAnalyzerRequest] = self._get_glue_data(glue_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(glue_names_policies)
        glue_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return glue_resources_for_region

    def _get_glue_data(self, glue_client) -> list[model.PolicyAnalyzerRequest]:
        glue_objects: list[GluePolicyTypeDef] = glue_client.get_resource_policies()
        return list(self.denormalize_to_glue_data(glue_data) for glue_data in glue_objects)

    @staticmethod
    def denormalize_to_glue_data(glue_data: GluePolicyTypeDef) -> model.PolicyAnalyzerRequest:
        if glue_data.get('PolicyInJson'):
            return DenormalizePolicyAnalyzerRequest().model(
                glue_data['PolicyHash'],
                glue_data['PolicyInJson']
            )


class ServerlessApplicationPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Serverless Application Policies in {region}")
        serverless_application_client = ServerlessApplicationRepository(self.account_id, region)
        serverless_application_data: list[model.ServerlessApplicationData] = self._get_applications_data(
            serverless_application_client)
        serverless_application_policies = self._get_serverless_application_policies(serverless_application_data,
                                                                                    serverless_application_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckServerlessAppRepoForOrganizationsDependency().scan(
            serverless_application_policies)
        serverless_application_policies_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
                resource, region) for resource in resources_dependent_on_organizations)
        return serverless_application_policies_for_region

    def _get_applications_data(self, serverless_application_client) -> list[model.ServerlessApplicationData]:
        serverless_application_objects: list[
            ApplicationSummaryTypeDef] = serverless_application_client.list_applications()
        return list(self.denormalize_to_serverless_application_data(serverless_application_data) for
                    serverless_application_data in serverless_application_objects)

    @staticmethod
    def denormalize_to_serverless_application_data(
            serverless_application_data: ApplicationSummaryTypeDef) -> model.ServerlessApplicationData:
        data: model.ServerlessApplicationData = {
            "ApplicationId": serverless_application_data['ApplicationId'],
            "Name": serverless_application_data['Name']
        }
        return data

    @staticmethod
    def _get_serverless_application_policies(serverless_application_data: list[model.ServerlessApplicationData],
                                             serverless_application_client) -> list[model.PolicyAnalyzerRequest]:
        serverless_application_policies = []
        for application in serverless_application_data:
            statements: list[ApplicationPolicyStatementTypeDef] = serverless_application_client.get_application_policy(
                application['ApplicationId']
            )
            if statements:
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    application['Name'],
                    json.dumps(statements)
                )
                serverless_application_policies.append(policy_object)
        return serverless_application_policies


class BackupVaultAccessPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Backup Vault Access Policies in {region}")
        backup_client = Backup(self.account_id, region)
        backup_data: list[model.BackupData] = self._get_backup_vault_data(
            backup_client)
        backup_policies = self._get_backup_policies(backup_data, backup_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(backup_policies)
        backup_policies_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
                resource, region) for resource in resources_dependent_on_organizations)
        return backup_policies_for_region

    def _get_backup_vault_data(self, backup_client) -> list[model.BackupData]:
        backup_objects: list[
            BackupVaultListMemberTypeDef] = backup_client.list_backup_vaults()
        return list(self.denormalize_to_backup_data(backup_data) for
                    backup_data in backup_objects)

    @staticmethod
    def denormalize_to_backup_data(backup_data: BackupVaultListMemberTypeDef) -> model.BackupData:
        data: model.BackupData = {
            "BackupVaultName": backup_data['BackupVaultName']
        }
        return data

    @staticmethod
    def _get_backup_policies(backup_data: list[model.BackupData],
                             backup_client) -> list[model.PolicyAnalyzerRequest]:
        backup_policies = []
        for vault in backup_data:
            policy: GetBackupVaultAccessPolicyOutputTypeDef = backup_client.get_backup_vault_access_policy(
                vault['BackupVaultName']
            )
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    policy.get('BackupVaultName'),
                    policy.get('Policy')
                )
                backup_policies.append(policy_object)
        return backup_policies


class CodeArtifactPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        code_artifact_policies_with_org_dependency_in_all_regions = []
        self.logger.info(f"Scanning CodeArtifact Domain and Repository Policies in {region}")
        codeartifact_client = CodeArtifact(self.account_id, region)
        code_artifact_domains_with_org_dependency = self.scan_code_artifact_domain_policy(
            region,
            codeartifact_client)
        code_artifact_repositories_with_org_dependency = self.scan_code_artifact_repository_policy(
            region,
            codeartifact_client)
        code_artifact_policies_with_org_dependency = [
            *code_artifact_domains_with_org_dependency,
            *code_artifact_repositories_with_org_dependency
        ]
        code_artifact_policies_with_org_dependency_in_all_regions.extend(code_artifact_policies_with_org_dependency)
        return code_artifact_policies_with_org_dependency_in_all_regions

    def scan_code_artifact_domain_policy(self, region, codeartifact_client) -> Iterable[
        model.ResourceBasedPolicyResponseModel]:
        domain_data: list[model.CodeArtifactDomainData] = self._get_domain_data(codeartifact_client)
        domain_names_documents = self._get_domain_names_and_documents(domain_data, codeartifact_client)
        iam_policies_with_org_condition: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(
            domain_names_documents)
        return list(DenormalizeResourceBasedPolicyResponse(self.event).model(resource, region) for resource in
                    iam_policies_with_org_condition)

    def _get_domain_data(self, codeartifact_client) -> list[model.CodeArtifactDomainData]:
        domain_objects: list[DomainSummaryTypeDef] = codeartifact_client.list_domains()
        return list(self.denormalize_to_iam_domain_data(domain) for domain in domain_objects)

    @staticmethod
    def denormalize_to_iam_domain_data(domain: DomainSummaryTypeDef) -> model.CodeArtifactDomainData:
        data: model.CodeArtifactDomainData = {
            'name': domain['name']
        }
        return data

    @staticmethod
    def _get_domain_names_and_documents(
            domain_data: list[model.CodeArtifactDomainData], codeartifact_client) -> list[model.PolicyAnalyzerRequest]:
        domain_policies = []
        for domain in domain_data:
            domain_policy_document: GetDomainPermissionsPolicyResultTypeDef = \
                codeartifact_client.get_domain_permissions_policy(domain['name'])
            if domain_policy_document.get('policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    f"{domain['name']}#Domain",  # CodeArtifact Domain and Repository can have same name
                    domain_policy_document.get('policy').get('document')
                )
                domain_policies.append(policy_object)
        return domain_policies

    def scan_code_artifact_repository_policy(self, region,
                                             codeartifact_client) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        repository_data: list[model.CodeArtifactRepoData] = self._get_repository_data(codeartifact_client)
        repository_names_documents = self._get_repository_names_and_documents(repository_data, codeartifact_client)
        iam_policies_with_org_condition: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(
            repository_names_documents)
        return list(DenormalizeResourceBasedPolicyResponse(self.event).model(resource, region) for resource in
                    iam_policies_with_org_condition)

    def _get_repository_data(self, codeartifact_client) -> list[model.CodeArtifactRepoData]:
        repository_objects: list[RepositorySummaryTypeDef] = codeartifact_client.list_repositories()
        return list(self.denormalize_to_iam_repository_data(repository) for repository in repository_objects)

    @staticmethod
    def denormalize_to_iam_repository_data(repository: RepositorySummaryTypeDef) -> model.CodeArtifactRepoData:
        data: model.CodeArtifactRepoData = {
            'name': repository['name'],
            'domainName': repository['domainName']
        }
        return data

    @staticmethod
    def _get_repository_names_and_documents(
            repository_data: list[model.CodeArtifactRepoData],
            codeartifact_client) -> list[model.PolicyAnalyzerRequest]:
        repository_policies = []
        for repository in repository_data:
            repository_policy_document: GetRepositoryPermissionsPolicyResultTypeDef = \
                codeartifact_client.get_repository_permissions_policy(
                    repository['domainName'],
                    repository['name']
                )
            if repository_policy_document.get('policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    f"{repository['name']}#Repository",  # CodeArtifact Domain and Repository can have same name
                    repository_policy_document.get('policy').get('document')
                )
                repository_policies.append(policy_object)
        return repository_policies


class CodeBuildResourcePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Code Build Resource Policies in {region}")
        code_build_client = CodeBuild(self.account_id, region)
        code_build_project_names = code_build_client.list_projects()
        code_build_project_data: list[model.CodeBuildData] = self._get_project_data(
            code_build_project_names,
            code_build_client
        ) if code_build_project_names else []
        code_built_report_group_data: list[model.CodeBuildData] = self._get_report_group_data(code_build_client)
        code_build_data = [*code_build_project_data, *code_built_report_group_data]
        code_build_resource_policies = self._get_code_build_resource_policies(code_build_data, code_build_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(code_build_resource_policies)
        code_build_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return code_build_resources_for_region

    def _get_project_data(self, code_build_project_names, code_build_client) -> list[model.CodeBuildData]:
        code_build_project_objects: list[ProjectTypeDef] = code_build_client.batch_get_projects(
            code_build_project_names)
        return list(self.denormalize_to_code_build_project_data(code_build_data) for code_build_data in
                    code_build_project_objects)

    @staticmethod
    def denormalize_to_code_build_project_data(code_build_data: ProjectTypeDef) -> model.CodeBuildData:
        data: model.CodeBuildData = {
            "arn": code_build_data['arn'],
            "name": code_build_data['name']
        }
        return data

    def _get_report_group_data(self, code_build_client) -> list[model.CodeBuildData]:
        code_built_report_group_arns = code_build_client.list_report_groups()
        return list(self.denormalize_to_code_build_report_group_data(report_group_arn) for report_group_arn in
                    code_built_report_group_arns)

    @staticmethod
    def denormalize_to_code_build_report_group_data(arn: str) -> model.CodeBuildData:
        data: model.CodeBuildData = {
            "arn": arn,
            "name": trim_string_from_front(
                get_name_from_arn(arn),
                remove='report/'
            )
        }
        return data

    @staticmethod
    def _get_code_build_resource_policies(
            code_build_data: list[model.CodeBuildData],
            code_build_client) -> list[model.PolicyAnalyzerRequest]:
        code_build_policies = []
        for resource in code_build_data:
            policy: GetResourcePolicyOutputTypeDef = code_build_client.get_resource_policy(
                resource['arn']
            )
            if policy.get('policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    resource['name'],
                    policy['policy']
                )
                code_build_policies.append(policy_object)
        return code_build_policies


class MediaStorePolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning Media Store Container Policies in {region}")
        media_store_client = MediaStore(self.account_id, region)
        media_store_container_names: list[model.MediaStoreContainerData] = self._get_media_store_container_names(
            media_store_client)
        media_store_names_policies: list[model.PolicyAnalyzerRequest] = self._get_media_store_data(
            media_store_container_names,
            media_store_client
        )
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(media_store_names_policies)
        media_store_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return media_store_resources_for_region

    def _get_media_store_container_names(self, media_store_client) -> list[model.MediaStoreContainerData]:
        container_objects: list[ContainerTypeDef] = media_store_client.list_containers()
        return list(self.denormalize_to_container_data(container_data) for container_data in
                    container_objects)

    @staticmethod
    def denormalize_to_container_data(container_data: ContainerTypeDef) -> model.MediaStoreContainerData:
        data: model.MediaStoreContainerData = {
            "Name": container_data['Name']
        }
        return data

    def _get_media_store_data(self, media_store_container_data: list[model.MediaStoreContainerData],
                              media_store_client) -> list[model.PolicyAnalyzerRequest]:
        container_policies = []
        for container in media_store_container_data:
            self.logger.debug(f"Getting Policy for {container}")
            policy: GetContainerPolicyOutputTypeDef = media_store_client.get_container_policy(
                container['Name']
            )
            if policy.get('Policy'):
                policy_object: model.PolicyAnalyzerRequest = DenormalizePolicyAnalyzerRequest().model(
                    container['Name'],
                    policy['Policy']
                )
                container_policies.append(policy_object)
        return container_policies


class VPCEndpointsPolicy:
    def __init__(self, event: model.ScanServiceRequestModel):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.event = event
        self.account_id = event['AccountId']

    def scan(self) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        return scan_regions(self.event, self.scan_single_region)

    def scan_single_region(self, region: str) -> Iterable[model.ResourceBasedPolicyResponseModel]:
        self.logger.info(f"Scanning VPC Endpoints Policies in {region}")
        ec2_client = EC2(self.account_id, region)
        vpc_endpoint_names_policies: list[model.PolicyAnalyzerRequest] = self._get_vpc_endpoint_names_policies(
            ec2_client)
        resources_dependent_on_organizations: list[
            model.PolicyAnalyzerResponse] = CheckForOrganizationsDependency().scan(vpc_endpoint_names_policies)
        vpc_endpoint_resources_for_region = list(DenormalizeResourceBasedPolicyResponse(self.event).model(
            resource, region) for resource in resources_dependent_on_organizations)
        return vpc_endpoint_resources_for_region

    def _get_vpc_endpoint_names_policies(self, ec2_client) -> list[model.PolicyAnalyzerRequest]:
        vpc_endpoint_objects: list[VpcEndpointTypeDef] = ec2_client.describe_vpc_endpoints()
        return list(self.denormalize_to_vpc_endpoint_data(vpc_endpoint_data) for vpc_endpoint_data in
                    vpc_endpoint_objects)

    @staticmethod
    def denormalize_to_vpc_endpoint_data(vpc_endpoint_data: VpcEndpointTypeDef) -> model.PolicyAnalyzerRequest:
        if vpc_endpoint_data.get('PolicyDocument'):
            return DenormalizePolicyAnalyzerRequest().model(
                vpc_endpoint_data['VpcEndpointId'],
                vpc_endpoint_data['PolicyDocument']
            )


class DenormalizePolicyAnalyzerRequest:
    def __init__(self):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))

    def model(self, resource_name: str, policy: str) -> model.PolicyAnalyzerRequest:
        request: model.PolicyAnalyzerRequest = {
            "ResourceName": resource_name,
            "Policy": policy
        }
        self.logger.debug(f"PolicyAnalyzerRequestModel: {model}")
        return request


class DenormalizeResourceBasedPolicyResponse:
    def __init__(self, event):
        self.event = event
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))

    def model(self, resource: model.PolicyAnalyzerResponse, region='global'):
        event: model.ScanServiceRequestModel = self.event
        response: model.ResourceBasedPolicyResponseModel = {
            'ServiceName': event['ServiceName'],
            'AccountId': event['AccountId'],
            'ResourceName': resource['ResourceName'],
            'DependencyType': resource['GlobalContextKey'],
            'DependencyOn': resource['OrganizationsResource'],
            'JobId': event['JobId'],
            'AssessedAt': datetime.now().isoformat(),
            'Region': region
        }
        self.logger.debug(f"ResourceBasedPolicyResponseModel: {model}")
        return response
