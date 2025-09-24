#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import TypedDict, List


class ScanModel(TypedDict):
    AccountIds: List[str]
    Regions: List[str]
    ServiceNames: List[str]


class ResourceBasedPolicyRequestModel(TypedDict):
    Scan: ScanModel
    JobId: str

class AccountValidationRequestModel(TypedDict):
    AccountId: str
    JobId: str
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
    Regions: list[str]


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
    

class ActionType(Enum):
    ALLOW = "Allow"
    DENY = "Deny"
    
class PrincipalType(Enum):
    PRINCIPAL = "Principal"
    NOT_PRINCIPAL = "NotPrincipal"
    
class ResourceType(Enum):
    RESOURCE = "Resource"
    NOT_RESOURCE = "NotResource"
    
class PolicyType(Enum):
    RESOURCE_BASED_POLICY = "ResourceBasedPolicy"
    IDENTITY_BASED_POLICY = "IdentityBasedPolicy"
    SERVICE_CONTROL_POLICY = "ServiceControlPolicy"
    
class KeyTypeToBeJSONFormatted(Enum):
    CONDITION = "Condition"
    PRINCIPAL = "Principal"
    RESOURCE = "Resource"
    ACTION = "Action"
    NOT_ACTION = "NotAction"
    NOT_RESOURCE = "NotResource"
    NOT_PRINCIPAL = "NotPrincipal"
    
class ValidateParameters(Enum):
    ACCOUNT_ID = "AccountId"
    POLICY_TYPE = "PolicyType"
    SERVICE = "Service"
    RESOURCE_IDENTIFIER = "ResourceIdentifier"
    REGION = "Region"
    POLICY = "Policy"


class DynamoDBPolicyItem(TypedDict):
    PartitionKey: str
    SortKey: str
    Region: str
    AccountId: str
    Action: str
    ActionType: ActionType
    Condition: str
    Effect: str
    Policy: str
    Principal: str
    PrincipalType: PrincipalType
    Resource: str
    ResourceIdentifier: str
    Service: str
    Sid: str
    ExpiresAt: int
    JobId: str | None


class PolicyItem(TypedDict):
    PartitionKey: str
    SortKey: str
    Region: str
    AccountId: str
    Action: str
    NotAction: str
    Condition: str
    Effect: str
    Policy: str
    Principal: str
    NotPrincipal: str
    Resource: str
    NotResource: str
    ResourceIdentifier: str
    Service: str
    ExpiresAt: int
    
    
class PolicyDetails(TypedDict):
    PolicyType: PolicyType
    Service: str
    ResourceIdentifier: str
    Region: str
    Policy: str | dict
    AccountId: str
    
class ParameterValidation(TypedDict):
    Key: str
    Value: str
    Message: str


class IAMPolicyData(TypedDict):
    Arn: str
    DefaultVersionId: str
    PolicyName: str


class S3Data(TypedDict):
    BucketName: str
    BucketRegion: str
    BucketAccountId: str


class LambdaFunctionData(TypedDict):
    FunctionName: str
    FunctionArn: str


class EFSData(TypedDict):
    FileSystemId: str
    FileSystemArn: str


class DescribeFileSystemPolicyResponse(TypedDict):
    FileSystemId: str
    Policy: str


class SecretsManagerData(TypedDict):
    Name: str
    Arn: str


class IoTData(TypedDict):
    PolicyName: str
    PolicyArn: str


class KMSData(TypedDict):
    KeyId: str
    KeyArn: str

class SESData(TypedDict):
    Identity: str
    PolicyNames: list


class ECRData(TypedDict):
    RepositoryName: str
    RepositoryArn: str


class SSMIncidentsData(TypedDict):
    arn: str
    name: str


class ConfigData(TypedDict):
    OrganizationConfigRuleName: str
    OrganizationConfigRuleArn: str


class OpenSearchData(TypedDict):
    DomainNames: list


class ServerlessApplicationData(TypedDict):
    ApplicationId: str
    Name: str
    Region: str


class BackupData(TypedDict):
    BackupVaultName: str
    BackupVaultArn: str


class CodeArtifactDomainData(TypedDict):
    Name: str
    Arn: str


class CodeArtifactRepoData(TypedDict):
    Name: str
    DomainName: str
    Arn: str


class MediaStoreContainerData(TypedDict):
    Name: str
    Arn: str


class CodeBuildData(TypedDict):
    Arn: str
    
class CloudFormationData(TypedDict):
    Name: str
    Arn: str
    
class GlacierVaultData(TypedDict):
    VaultName: str
    VaultArn: str
    
class IAMRoleInlinePolicyData(TypedDict):
    RoleName: str
    PolicyNames: list[str]
    RoleArn: str

class ServiceControlPolicySummary(TypedDict):
    Arn: str
    Id: str


class PolicyFilters(TypedDict):
    AccountId: str | None
    Action: str | None
    NotAction: str | None
    Condition: str | None
    Principal: str | None
    NotPrincipal: str | None
    Resource: str | None
    NotResource: str | None
    Effect: str | None


class DdbPagination(TypedDict):
    Limit: int
    ExclusiveStartKey: str | None


class PaginationMetadata(TypedDict):
    nextToken: str | None
    hasMoreResults: bool


class PolicySearchResponse(TypedDict):
    Results: List[PolicyItem]
    Pagination: PaginationMetadata
