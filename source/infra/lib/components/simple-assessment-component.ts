// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {Construct} from "constructs";
import {AttributeType, BillingMode, Table, TableEncryption} from "aws-cdk-lib/aws-dynamodb";
import {CfnParameter, Duration} from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import {AssetCode, Runtime} from "aws-cdk-lib/aws-lambda";
import {CfnPolicy, CfnRole, PolicyStatement} from "aws-cdk-lib/aws-iam";
import {
  AuthorizationType,
  LambdaIntegration,
  Model,
  ModelProps,
  RequestValidator,
  RestApi
} from "aws-cdk-lib/aws-apigateway";
import {CognitoAuthenticationResources} from "./cognito-authenticator";
import {addCfnSuppressRules} from "@aws-solutions-constructs/core";
import {ORG_MANAGEMENT_ROLE_NAME} from "../org-management-account-stack";

export interface AssessmentComponentProps {
  cognitoAuthenticationResources: CognitoAuthenticationResources,
  tables: {
    jobHistory: Table,
  },
  functions: { deleteJob: lambda.Function }
  api: RestApi,
  componentConfig: {
    readHandlerPath: string,
    scanHandlerPath?: string,
    apiResourcePath: string,
    tableEnvVariableName: string,
    powertoolsServiceName: string
    dynamoTtlInDays: CfnParameter,
    solutionVersion: string,
    stackId: string,
    sendAnonymousData: string
  },
  requestValidation?: {
    scanRequestBodyModelProps: ModelProps
  },
  assetCode: AssetCode,
  namespace: CfnParameter,
  region: string
}

export class SimpleAssessmentComponent extends Construct {

  public readonly componentTable: Table;
  public readonly functions: { readFunction: lambda.Function; scanFunction?: lambda.Function };

  constructor(scope: Construct, id: string, {
    cognitoAuthenticationResources,
    tables,
    functions,
    api,
    assetCode,
    componentConfig,
    namespace,
    requestValidation,
    region
  }: AssessmentComponentProps) {
    super(scope, id);

    const {
      readHandlerPath,
      scanHandlerPath,
      apiResourcePath,
      tableEnvVariableName,
      powertoolsServiceName
    } = componentConfig;

    this.componentTable = new Table(this, 'Table', {
      partitionKey: {
        name: 'PartitionKey',
        type: AttributeType.STRING
      },
      sortKey: {
        name: 'SortKey',
        type: AttributeType.STRING
      },
      encryption: TableEncryption.AWS_MANAGED,
      billingMode: BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
      timeToLiveAttribute: 'ExpiresAt',
    });
    this.componentTable.grantReadWriteData(functions.deleteJob);
    this.componentTable.addGlobalSecondaryIndex({
      indexName: 'JobId',
      partitionKey: {name: 'JobId', type: AttributeType.STRING},
    });


    // has to match AssessmentType. referenced via DynamoDB(os.getenv(assessment_type))
    functions.deleteJob.addEnvironment(tableEnvVariableName, this.componentTable.tableName);

    const readFunction = new lambda.Function(this, 'Read', {
      runtime: Runtime.PYTHON_3_12,
      tracing: lambda.Tracing.ACTIVE,
      timeout: Duration.minutes(1),
      code: assetCode,
      handler: readHandlerPath,
      environment: {
        COMPONENT_TABLE: this.componentTable.tableName,
        TABLE_JOBS: tables.jobHistory.tableName,
        POWERTOOLS_SERVICE_NAME: 'Read' + powertoolsServiceName,
        SOLUTION_VERSION: componentConfig.solutionVersion,
        STACK_ID: componentConfig.stackId,
        SEND_ANONYMOUS_DATA: componentConfig.sendAnonymousData
      }
    });

    let scanFunction = undefined

    if (scanHandlerPath && scanHandlerPath != "")  {
      scanFunction = new lambda.Function(this, 'StartScan', {
        runtime: Runtime.PYTHON_3_12,
        tracing: lambda.Tracing.ACTIVE,
        timeout: Duration.minutes(2),
        code: assetCode,
        handler: scanHandlerPath,
        environment: {
          COMPONENT_TABLE: this.componentTable.tableName,
          TABLE_JOBS: tables.jobHistory.tableName,
          TIME_TO_LIVE_IN_DAYS: componentConfig.dynamoTtlInDays.valueAsString,
          ORG_MANAGEMENT_ROLE_NAME: `${namespace.valueAsString}-${region}-${ORG_MANAGEMENT_ROLE_NAME}`,
          LOG_LEVEL: 'INFO',
          POWERTOOLS_SERVICE_NAME: 'Scan' + powertoolsServiceName,
          SOLUTION_VERSION: componentConfig.solutionVersion,
          STACK_ID: componentConfig.stackId,
          SEND_ANONYMOUS_DATA: componentConfig.sendAnonymousData
        }
      });

      const validateAccountAccessRole_cfn_ref = scanFunction.role?.node.defaultChild as CfnRole
      validateAccountAccessRole_cfn_ref.roleName = `${namespace.valueAsString}-${region}-${powertoolsServiceName}`

      scanFunction.addToRolePolicy(new PolicyStatement({
        actions: ['organizations:DescribeOrganization'],
        resources: ["*"],
      }));
      scanFunction.addToRolePolicy(new PolicyStatement({
        actions: ['sts:AssumeRole'],
        resources: [`arn:aws:iam::*:role/${namespace.valueAsString}-${region}-${ORG_MANAGEMENT_ROLE_NAME}`],
      }));
      const scanFunctionDefaultPolicy = scanFunction.node.tryFindChild('ServiceRole')
        ?.node.findChild('DefaultPolicy')
        .node.findChild('Resource') as CfnPolicy;
      scanFunctionDefaultPolicy && addCfnSuppressRules(scanFunctionDefaultPolicy, [{
        id: 'W12',
        reason: 'Resource * is necessary for organizations:List* operations. No risk, because the role can still only access its own organization.'
      }]);
      this.componentTable.grantReadWriteData(scanFunction);
      tables.jobHistory.grantReadWriteData(scanFunction);
  }


    // Grant the Lambda function read access to the DynamoDB table
    this.componentTable.grantReadData(readFunction);
    tables.jobHistory.grantReadData(readFunction);

    const validatorProps = requestValidation ? {
      requestValidator: new RequestValidator(this, 'RequestBodyValidator', {
        restApi: api,
        validateRequestBody: true,
        validateRequestParameters: false
      }),
      requestModels: {
        "application/json": new Model(this, "ScanConfigModel", requestValidation.scanRequestBodyModelProps),
      },
    } : {};

    
    const apiResource = api.root.addResource(apiResourcePath);
    apiResource.addMethod('GET', new LambdaIntegration(readFunction), {
      authorizationType: AuthorizationType.COGNITO,
      authorizer: {
        authorizerId: cognitoAuthenticationResources.authorizerFullAccess.ref
      },
      authorizationScopes: ['account-assessment-api/api'],
    });

    if (scanFunction) {
      apiResource.addMethod('POST', new LambdaIntegration(scanFunction), {
        authorizationType: AuthorizationType.COGNITO,
        authorizer: {
          authorizerId: cognitoAuthenticationResources.authorizerFullAccess.ref
        },
        authorizationScopes: ['account-assessment-api/api'],
        ...validatorProps
      });
    }
    
    this.functions = {scanFunction, readFunction};
  }

}
