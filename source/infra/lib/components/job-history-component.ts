// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {Construct} from "constructs";
import {AttributeType, BillingMode, Table, TableEncryption} from "aws-cdk-lib/aws-dynamodb";
import {CfnParameter, Duration} from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import {AssetCode, Runtime} from "aws-cdk-lib/aws-lambda";
import {AuthorizationType, LambdaIntegration, RestApi} from "aws-cdk-lib/aws-apigateway";
import {CognitoAuthenticationResources} from "./cognito-authenticator";

type JobHistoryComponentProps = {
  cognitoAuthenticationResources: CognitoAuthenticationResources,
  api: RestApi,
  assetCode: AssetCode,
  dynamoTtlInDays: CfnParameter,
  solutionVersion: string,
  stackId: string
  sendAnonymousData: string
};

export class JobHistoryComponent extends Construct {
  public readonly jobHistoryTable: Table;
  public readonly sharedFunctions: { deleteJob: lambda.Function };

  constructor(scope: Construct, id: string, {
    api, assetCode, cognitoAuthenticationResources, dynamoTtlInDays, solutionVersion, stackId, sendAnonymousData
  }: JobHistoryComponentProps) {
    super(scope, id);

    const jobHistoryTable = new Table(this, 'Table', {
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
    this.jobHistoryTable = jobHistoryTable;

    const jobsApiHandler = new lambda.Function(this, 'JobsHandler', {
      runtime: Runtime.PYTHON_3_12,
      tracing: lambda.Tracing.ACTIVE,
      timeout: Duration.minutes(1),
      code: assetCode,
      handler: 'assessment_runner/api_router.lambda_handler',
      environment: {
        TABLE_JOBS: jobHistoryTable.tableName,
        POWERTOOLS_LOGGER_LOG_EVENT: 'True',
        POWERTOOLS_SERVICE_NAME: 'JobsApiHandler',
        TIME_TO_LIVE_IN_DAYS: dynamoTtlInDays.valueAsString,
        SOLUTION_VERSION: solutionVersion,
        STACK_ID: stackId,
        SEND_ANONYMOUS_DATA: sendAnonymousData
      }
    });
    jobHistoryTable.grantReadWriteData(jobsApiHandler);

    const jobsResource = api.root.addResource('jobs');
    const proxyOptions = {
      apiKeyRequired: false,
      authorizationType: AuthorizationType.COGNITO,
      authorizer: {
        authorizerId: cognitoAuthenticationResources.authorizerFullAccess.ref
      },
      authorizationScopes: ['account-assessment-api/api'],
    };
    jobsResource.addMethod('GET', new LambdaIntegration(jobsApiHandler), proxyOptions);
    const jobResource = jobsResource.addResource('{assessmentType}').addResource('{id}');
    jobResource.addMethod('GET', new LambdaIntegration(jobsApiHandler), proxyOptions);
    jobResource.addMethod('DELETE', new LambdaIntegration(jobsApiHandler), proxyOptions);

    this.sharedFunctions = {
      deleteJob: jobsApiHandler
    }
  }

}
