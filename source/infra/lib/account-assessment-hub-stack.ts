// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as cdk from 'aws-cdk-lib';
import {CfnParameter} from 'aws-cdk-lib';
import {Construct} from "constructs";
import {SimpleAssessmentComponent} from "./components/simple-assessment-component";
import {JobHistoryComponent} from "./components/job-history-component";
import {WebUIDeployer} from "./components/web-ui-deployer";
import {CognitoAuthenticator} from "./components/cognito-authenticator";
import {WebUIHosting} from "./components/web-ui-hosting";
import {Api} from "./components/api";
import {Code} from "aws-cdk-lib/aws-lambda";
import * as path from "path";
import * as iam from 'aws-cdk-lib/aws-iam';
import {PolicyExplorerScanComponent} from './components/policy-explorer';

export const TRUSTED_ACCESS_SCAN = 'TrustedAccess'
export const DELEGATED_ADMIN_SCAN = 'DelegatedAdmin'
export const RESOURCE_BASED_POLICY_SCAN = 'ResourceBasedPolicy'
export const POLICY_EXPLORER_SCAN = 'PolicyExplorer'

export interface AccountAssessmentHubStackProps extends cdk.StackProps {
  solutionId: string;
  solutionTradeMarkName: string;
  solutionProvider: string;
  solutionBucketName: string;
  solutionName: string;
  solutionVersion: string;
}

export class AccountAssessmentHubStack extends cdk.Stack {
  public appRegisterData: { managementAccountId: string; orgId: string };

  constructor(scope: Construct, id: string, private props: AccountAssessmentHubStackProps) {
    super(scope, id, props);

    const allowListedIPRanges = new CfnParameter(this, 'AllowListedIPRanges', {
      description: 'Comma separated list of CIDR ranges that allow access to the API. To allow all the entire internet, use 0.0.0.0/1,128.0.0.0/1',
      type: 'CommaDelimitedList',
      default: '0.0.0.0/1,128.0.0.0/1'
    });

    const namespace = new CfnParameter(this, 'DeploymentNamespace', {
      description: 'This value is used as prefix for resource names. Same namespace must be used in spoke stack and management account stack.',
      maxLength: 10,
      type: 'String'
    });

    const orgId = new CfnParameter(this, "OrganizationID", {
      description:
        "Organization ID",
      type: "String",
      allowedPattern: "^$|^o-[a-z0-9]{10,32}$",
    });

    const managementAccountId = new CfnParameter(
      this,
      "ManagementAccountId",
      {
        description:
          "Account ID for the management account of the Organization.",
        type: "String",
      }
    );
    this.appRegisterData = {
      orgId: orgId.valueAsString,
      managementAccountId: managementAccountId.valueAsString
    }

    const api = new Api(this, 'Api', {region: this.region, allowListedIPRanges, namespace});

    const lambdaZip = Code.fromAsset(
      `${path.dirname(__dirname)}/../../deployment/regional-s3-assets/lambda.zip`
    );

    const {cloudFrontToS3, s3BucketInterface} = new WebUIHosting(this, 'WebUIHosting', {namespace});


    const dynamoTtlInDays = new CfnParameter(this, 'DynamoTimeToLive', {
      default: 90,
      description: 'DynamoDB will delete each stored Item after the given time. This value will be applicable to all the DynamoDB tables.',
      type: 'Number'
    });

    const multiFactorAuthentication = new CfnParameter(this, 'MultiFactorAuthentication', {
      description: "Set to 'ON' or 'OPTIONAL' to enable multi factor authentication for Cognito User Pool.",
      default: 'OPTIONAL',
      allowedValues: ['ON', 'OPTIONAL'],
      type: 'String'
    });

    const userEmail = new CfnParameter(this, 'UserEmail', {
      allowedPattern: '^(([^<>()\\[\\]\\\\.,;:\\s@"]+(\\.[^<>()\\[\\]\\\\.,;:\\s@"]+)*)|(".+"))@((\\[[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}])|(([a-zA-Z\\-0-9]+\\.)+[a-zA-Z]{2,}))$', // source: http://emailregex.com/
      description: 'Admin user will be created at deployment time. Provide an email address to create this initial Cognito user.',
      type: 'String'
    });

    const cognitoAuthenticationResources = new CognitoAuthenticator(this, 'Auth', {
      domainName: cloudFrontToS3.cloudFrontWebDistribution.domainName,
      region: this.region,
      restApiId: api.restApi.restApiId,
      emailTitle: "Account Assessment for AWS Organizations",
      emailSubject: "WebUI Credentials - Account Assessment for AWS Organizations",
      cognitoDomainPrefix: namespace.valueAsString + '-' + this.account,
      multiFactorAuthentication,
      userEmail,
      assetCode: lambdaZip
    }).cognitoAuthenticationResources


    this.templateOptions.metadata = {
      "AWS::CloudFormation::Interface": {
        ParameterGroups: [
          {
            Label: {default: "Solution Setup"},
            Parameters: [namespace.logicalId, orgId.logicalId]
          },
          {
            Label: {default: "DynamoDB Configuration"},
            Parameters: [dynamoTtlInDays.logicalId]
          },
          {
            Label: {default: "Web UI Configuration"},
            Parameters: [userEmail.logicalId, multiFactorAuthentication.logicalId]
          },
          {
            Label: {default: "Security Configuration"},
            Parameters: [allowListedIPRanges.logicalId]
          },
          {
            Label: {default: "Application Manager Configuration"},
            Parameters: [managementAccountId.logicalId]
          }
        ],
        ParameterLabels: {
          [namespace.logicalId]: {
            default: "Provide a unique namespace value.",
          },
          [orgId.logicalId]: {
            default: "Provide the AWS Organization ID",
          },
          [dynamoTtlInDays.logicalId]: {
            default: "Provide Time to live (in days) for DynamoDB items.",
          },
          [userEmail.logicalId]: {
            default: "Provide Web UI Login User Email",
          },
          [multiFactorAuthentication.logicalId]: {
            default: "Set MFA for Cognito to 'ON' or 'OPTIONAL'",
          },
          [allowListedIPRanges.logicalId]: {
            default: "Provide CIDR ranges that allow to console to access the API.",
          },
          [managementAccountId.logicalId]: {
            default: "Provide the Org Management Account ID",
          }
        },
      },
    };

    const mappings = new cdk.CfnMapping(this, "AnonymousData")
    mappings.setValue("SendAnonymousData", "Data", 'Yes')

    const jobHistory = new JobHistoryComponent(this, 'JobHistory', {
      cognitoAuthenticationResources,
      api: api.restApi,
      assetCode: lambdaZip,
      dynamoTtlInDays,
      solutionVersion: props.solutionVersion,
      stackId: this.stackId,
      sendAnonymousData: mappings.findInMap("SendAnonymousData", "Data")
    });

    new SimpleAssessmentComponent(this, 'DelegatedAdmins', {
      cognitoAuthenticationResources,
      tables: {jobHistory: jobHistory.jobHistoryTable},
      functions: {deleteJob: jobHistory.sharedFunctions.deleteJob},
      api: api.restApi,
      componentConfig: {
        readHandlerPath: 'delegated_admins/read_delegated_admins.lambda_handler',
        scanHandlerPath: 'delegated_admins/scan_for_delegated_admins.lambda_handler',
        apiResourcePath: 'delegated-admins',
        tableEnvVariableName: 'TABLE_DELEGATED_ADMIN',
        powertoolsServiceName: DELEGATED_ADMIN_SCAN,
        dynamoTtlInDays,
        solutionVersion: props.solutionVersion,
        stackId: this.stackId,
        sendAnonymousData: mappings.findInMap("SendAnonymousData", "Data")
      },
      assetCode: lambdaZip,
      namespace,
      region: this.region
    });

    new SimpleAssessmentComponent(this, 'TrustedAccess', {
      cognitoAuthenticationResources,
      tables: {jobHistory: jobHistory.jobHistoryTable},
      functions: {deleteJob: jobHistory.sharedFunctions.deleteJob},
      api: api.restApi,
      componentConfig: {
        readHandlerPath: 'trusted_access_enabled_services/read_trusted_services.lambda_handler',
        scanHandlerPath: 'trusted_access_enabled_services/scan_for_trusted_services.lambda_handler',
        apiResourcePath: 'trusted-access',
        tableEnvVariableName: 'TABLE_TRUSTED_ACCESS',
        powertoolsServiceName: TRUSTED_ACCESS_SCAN,
        dynamoTtlInDays,
        solutionVersion: props.solutionVersion,
        stackId: this.stackId,
        sendAnonymousData: mappings.findInMap("SendAnonymousData", "Data")
      },
      assetCode: lambdaZip,
      namespace,
      region: this.region
    });

    new SimpleAssessmentComponent(this, 'ResourceBasedPolicy', {
      cognitoAuthenticationResources,
      tables: {jobHistory: jobHistory.jobHistoryTable},
      functions: {deleteJob: jobHistory.sharedFunctions.deleteJob},
      api: api.restApi,
      componentConfig: {
        readHandlerPath: 'resource_based_policy/read_resource_based_policies.lambda_handler',
        apiResourcePath: 'resource-based-policies',
        tableEnvVariableName: 'TABLE_RESOURCE_BASED_POLICY',
        powertoolsServiceName: RESOURCE_BASED_POLICY_SCAN,
        dynamoTtlInDays,
        solutionVersion: props.solutionVersion,
        stackId: this.stackId,
        sendAnonymousData: mappings.findInMap("SendAnonymousData", "Data")
      },
      assetCode: lambdaZip,
      namespace,
      region: this.region
    });

    new WebUIDeployer(this, 'WebUIDeployer', {
      region: this.region,
      orgId: orgId.valueAsString,
      apiGatewayUrl: api.apiGatewayUrl,
      deploymentBucket: s3BucketInterface,
      cloudFront: cloudFrontToS3.cloudFrontWebDistribution,
      auth: cognitoAuthenticationResources,
      deploymentSourceBucketName: props.solutionBucketName,
      deploymentSourcePath: `${this.props.solutionTradeMarkName}/${this.props.solutionVersion}/webui/`,
      assetCode: lambdaZip,
      solutionVersion: props.solutionVersion,
      stackId: this.stackId,
      sendAnonymousData: mappings.findInMap("SendAnonymousData", "Data")
    })
    
    new PolicyExplorerScanComponent(this, 'PolicyExplorer', {
      cognitoAuthenticationResources,
      api: api.restApi,
      assetCode: lambdaZip,
      tables: {jobHistory: jobHistory.jobHistoryTable},
      functions: {deleteJob: jobHistory.sharedFunctions.deleteJob},
      apiResourcePath: 'policy-explorer',
      componentTableConfig: {
        partitionKeyName: 'PartitionKey',
        sortKeyName: 'SortKey',
      },
      componentConfig: {
        readHandlerPath: 'policy_explorer/read_policies.lambda_handler',
        apiResourcePath: 'policy-explorer',
        tableEnvVariableName: 'TABLE_POLICY_EXPLORER',
        powertoolsServiceName: POLICY_EXPLORER_SCAN,
        dynamoTtlInDays,
        solutionVersion: props.solutionVersion,
        stackId: this.stackId,
        sendAnonymousData: mappings.findInMap("SendAnonymousData", "Data")
      },
      roleAssumedByApiGateway: new iam.ServicePrincipal('apigateway.amazonaws.com'),
      dynamoDbRoleName: 'DynamoDbRole',
      namespace,
      region: this.region,
      partition: this.partition,
      accountId: this.account,
    })
    
  }
}
