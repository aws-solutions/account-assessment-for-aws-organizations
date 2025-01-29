#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from typing import Dict, List

SUPPORTED_SERVICES = [
    {
        "ServiceName": "iam",
        "ServicePrincipal": "iam.amazonaws.com",
        "FriendlyName": "AWS Identity and Access Management (AWS IAM)"
    },
    {
        "ServiceName": "s3",
        "ServicePrincipal": "s3.amazonaws.com",
        "FriendlyName": "Amazon S3 (Amazon Simple Storage Service)"
    },
    {
        "ServiceName": "glacier",
        "ServicePrincipal": "glacier.amazonaws.com",
        "FriendlyName": "Amazon S3 Glacier"
    },
    {
        "ServiceName": "sns",
        "ServicePrincipal": "sns.amazonaws.com",
        "FriendlyName": "Amazon Simple Notification Service (Amazon SNS)"
    },
    {
        "ServiceName": "sqs",
        "ServicePrincipal": "sqs.amazonaws.com",
        "FriendlyName": "Amazon Simple Queue Service (Amazon SQS)"
    },
    {
        "ServiceName": "lambda",
        "ServicePrincipal": "lambda.amazonaws.com",
        "FriendlyName": "AWS Lambda"
    },
    {
        "ServiceName": "elasticfilesystem",
        "ServicePrincipal": "elasticfilesystem.amazonaws.com",
        "FriendlyName": "Amazon Elastic File System (Amazon EFS)"
    },
    {
        "ServiceName": "secretsmanager",
        "ServicePrincipal": "secretsmanager.amazonaws.com",
        "FriendlyName": "AWS Secrets Manager"
    },
    {
        "ServiceName": "iot",
        "ServicePrincipal": "iot.amazonaws.com",
        "FriendlyName": "AWS IoT"
    },
    {
        "ServiceName": "kms",
        "ServicePrincipal": "kms.amazonaws.com",
        "FriendlyName": "AWS Key Management Service (KMS)"
    },
    {
        "ServiceName": "apigateway",
        "ServicePrincipal": "apigateway.amazonaws.com",
        "FriendlyName": "Amazon API Gateway"
    },
    {
        "ServiceName": "events",
        "ServicePrincipal": "events.amazonaws.com",
        "FriendlyName": "Amazon EventBridge"
    },
    {
        "ServiceName": "ses",
        "ServicePrincipal": "ses.amazonaws.com",
        "FriendlyName": "Amazon Simple Email Service (SES)"
    },
    {
        "ServiceName": "ecr",
        "ServicePrincipal": "ecr.amazonaws.com",
        "FriendlyName": "Amazon Elastic Container Registry"
    },
    {
        "ServiceName": "config",
        "ServicePrincipal": "config.amazonaws.com",
        "FriendlyName": "AWS Config"
    },
    {
        "ServiceName": "ssm_incidents",
        "ServicePrincipal": "ssm-incidents.amazonaws.com",
        "FriendlyName": "AWS Systems Manager Incident Manager"
    },
    {
        "ServiceName": "opensearchservice",
        "ServicePrincipal": "opensearchservice.amazonaws.com",
        "FriendlyName": "Amazon OpenSearch Service"
    },
    {
        "ServiceName": "cloudformation",
        "ServicePrincipal": "cloudformation.amazonaws.com",
        "FriendlyName": "AWS CloudFormation"
    },
    {
        "ServiceName": "glue",
        "ServicePrincipal": "glue.amazonaws.com",
        "FriendlyName": "AWS Glue"
    },
    {
        "ServiceName": "serverlessrepo",
        "ServicePrincipal": "serverlessrepo.amazonaws.com",
        "FriendlyName": "AWS Serverless Application Repository"
    },
    {
        "ServiceName": "backup",
        "ServicePrincipal": "backup.amazonaws.com",
        "FriendlyName": "AWS Backup"
    },
    {
        "ServiceName": "codeartifact",
        "ServicePrincipal": "codeartifact.amazonaws.com",
        "FriendlyName": "AWS CodeArtifact"
    },
    {
        "ServiceName": "codebuild",
        "ServicePrincipal": "codebuild.amazonaws.com",
        "FriendlyName": "AWS CodeBuild"
    },
    {
        "ServiceName": "mediastore",
        "ServicePrincipal": "mediastore.amazonaws.com",
        "FriendlyName": "AWS Elemental MediaStore"
    },
    {
        "ServiceName": "ec2",
        "ServicePrincipal": "ec2.amazonaws.com",
        "FriendlyName": "Amazon VPC (VPC Endpoints)"
    },
    {
        "ServiceName": "lexv2",
        "ServicePrincipal": "lexv2.amazonaws.com",
        "FriendlyName": "Amazon Lex"
    },
    {
        "ServiceName": "redshift_serverless",
        "ServicePrincipal": "redshift.amazonaws.com",
        "FriendlyName": "Amazon Redshift Serverless"
    },
    {
        "ServiceName": "eventbridge_schemas",
        "ServicePrincipal": "events.amazonaws.com",
        "FriendlyName": "Amazon EventBridge Schemas"
    },
     {
        "ServiceName": "ssm_contacts",
        "ServicePrincipal": "ssm-contacts.amazonaws.com",
        "FriendlyName": "AWS Systems Manager Incident Manager Contacts"
    },
    {
        "ServiceName": "acm_pca",
        "ServicePrincipal": "acm-pca.amazonaws.com",
        "FriendlyName": "AWS Private Certificate Authority"
    },
    {
        "ServiceName": "ram",
        "ServicePrincipal": "ram.amazonaws.com",
        "FriendlyName": "AWS Resource Access Manager"
    }
]
SUPPORTED_SERVICE_NAMES = list(service_data['ServiceName'] for service_data in SUPPORTED_SERVICES)

SUPPORTED_REGIONS = [
    {
        "Region": "GLOBAL",
        "RegionName": "Global"
    },
    {
        "Region": "us-east-1",
        "RegionName": "US East (N. Virginia)"
    },
    {
        "Region": "us-east-2",
        "RegionName": "US East (Ohio)"
    },
    {
        "Region": "us-west-1",
        "RegionName": "US West (N. California)"
    },
    {
        "Region": "us-west-2",
        "RegionName": "US West (Oregon)"
    },
    {
        "Region": "af-south-1",
        "RegionName": "Africa (Cape Town) [Opt-In Required]"
    },
    {
        "Region": "ap-east-1",
        "RegionName": "Asia Pacific (Hong Kong) [Opt-In Required]"
    },
    {
        "Region": "ap-southeast-1",
        "RegionName": "Asia Pacific (Singapore)"
    },
    {
        "Region": "ap-southeast-2",
        "RegionName": "Asia Pacific (Sydney)"
    },
    {
        "Region": "ap-southeast-3",
        "RegionName": "Asia Pacific (Jakarta) [Opt-In Required]"
    },
    {
        "Region": "ap-south-1",
        "RegionName": "Asia Pacific (Mumbai)"
    },
    {
        "Region": "ap-northeast-3",
        "RegionName": "Asia Pacific (Osaka)"
    },
    {
        "Region": "ap-northeast-2",
        "RegionName": "Asia Pacific (Seoul)"
    },
    {
        "Region": "ap-northeast-1",
        "RegionName": "Asia Pacific (Tokyo)"
    },
    {
        "Region": "ca-central-1",
        "RegionName": "Canada (Central)"
    },
    {
        "Region": "eu-central-1",
        "RegionName": "Europe (Frankfurt)"
    },
    {
        "Region": "eu-west-3",
        "RegionName": "Europe (Paris)"
    },
    {
        "Region": "eu-west-2",
        "RegionName": "Europe (London)"
    },
    {
        "Region": "eu-west-1",
        "RegionName": "Europe (Ireland)"
    },
    {
        "Region": "eu-north-1",
        "RegionName": "Europe (Stockholm)"
    },
    {
        "Region": "eu-south-1",
        "RegionName": "Europe (Milan) [Opt-In Required]"
    },
    {
        "Region": "me-south-1",
        "RegionName": "Middle East (Bahrain) [Opt-In Required]"
    },
    {
        "Region": "me-central-1",
        "RegionName": "Middle East (UAE) [Opt-In Required]"
    },
    {
        "Region": "sa-east-1",
        "RegionName": "South America (São Paulo)"
    }
]


class SupportedRegions:
    @staticmethod
    def get_supported_region_objects() -> List[dict]:
        return SUPPORTED_REGIONS

    @staticmethod
    def regions() -> List[str]:
        return list(it['Region'] for it in SUPPORTED_REGIONS)


class SupportedServices:
    @staticmethod
    def service_names() -> List[str]:
        return list(it['ServiceName'] for it in SUPPORTED_SERVICES)

    @staticmethod
    def service_principals() -> List[str]:
        return list(it['ServicePrincipal'] for it in SUPPORTED_SERVICES)

    @staticmethod
    def get_supported_services() -> List[Dict]:
        return SUPPORTED_SERVICES
