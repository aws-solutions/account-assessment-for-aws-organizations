# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import TypedDict, List

from utils.base_repository import FindingModel


class ScanModel(TypedDict):
    AccountIds: List[str]
    Regions: List[str]
    ServiceNames: List[str]


class ResourceBasedPolicyRequestModel(TypedDict):
    Scan: ScanModel
    JobId: str


class ResourceBasedPolicyDBModel(FindingModel):
    AccountId: str
    ServiceName: str
    ResourceName: str
    DependencyType: str
    DependencyOn: str
    Region: str


# Keep in sync with ResourceBasedPolicyModel.ts in the UI project
class ResourceBasedPolicyResponseModel(TypedDict):
    AccountId: str
    ServiceName: str
    ResourceName: str
    DependencyType: str
    DependencyOn: str
    JobId: str
    AssessedAt: str
    Region: str


class AccountValidationRequestModel(TypedDict):
    AccountId: str
    JobId: str
    Regions: list[str]
    ServiceNames: list[str]


class ScanServiceRequestModel(TypedDict):
    AccountId: str
    JobId: str
    Regions: list[str]
    ServiceName: str


class ValidationType(Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class AccountValidationResponseModel(TypedDict):
    Validation: str
    ServicesToScanForAccount: List[str]


class PolicyStatementModel(TypedDict):
    Effect: str
    Principal: dict
    Action: str  # or list
    Resource: str  # or list
    Condition: dict


class PolicyDocumentModel(TypedDict):
    Version: str
    Id: str
    Statement: list[PolicyStatementModel]


class PolicyAnalyzerRequest(TypedDict):
    ResourceName: str
    Policy: str


class PolicyAnalyzerResponse(TypedDict):
    ResourceName: str
    GlobalContextKey: str
    OrganizationsResource: str


class IAMPolicyData(TypedDict):
    Arn: str
    DefaultVersionId: str
    PolicyName: str


class S3Data(TypedDict):
    BucketName: str
    BucketRegion: str


class LambdaFunctionData(TypedDict):
    FunctionName: str


class EFSData(TypedDict):
    FileSystemId: str


class DescribeFileSystemPolicyResponse(TypedDict):
    FileSystemId: str
    Policy: str


class SecretsManagerData(TypedDict):
    Name: str


class IoTData(TypedDict):
    policyName: str


class KMSData(TypedDict):
    KeyId: str


class SESData(TypedDict):
    Identity: str
    PolicyNames: list


class ECRData(TypedDict):
    repositoryName: str


class SSMIncidentsData(TypedDict):
    arn: str
    name: str


class ConfigData(TypedDict):
    OrganizationConfigRuleName: str


class OpenSearchData(TypedDict):
    DomainNames: list


class ServerlessApplicationData(TypedDict):
    ApplicationId: str
    Name: str


class BackupData(TypedDict):
    BackupVaultName: str


class CodeArtifactDomainData(TypedDict):
    name: str


class CodeArtifactRepoData(TypedDict):
    name: str
    domainName: str


class MediaStoreContainerData(TypedDict):
    Name: str


class CodeBuildData(TypedDict):
    name: str
    arn: str