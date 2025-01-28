// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {Construct} from "constructs";
import * as cdk from "aws-cdk-lib";
import {CustomResource} from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import {AssetCode, Runtime} from "aws-cdk-lib/aws-lambda";
import {CognitoAuthenticationResources} from "./cognito-authenticator";
import {Bucket, IBucket} from "aws-cdk-lib/aws-s3";
import {Distribution} from "aws-cdk-lib/aws-cloudfront";

type WebUIDeployerProps = {
  region: string,
  orgId: string,
  apiGatewayUrl: string,
  deploymentBucket: IBucket,
  cloudFront: Distribution,
  auth: CognitoAuthenticationResources,
  deploymentSourceBucketName: string
  deploymentSourcePath: string,
  assetCode: AssetCode,
  solutionVersion: string,
  stackId: string,
  sendAnonymousData: string
};

export class WebUIDeployer extends Construct {

  constructor(scope: Construct, id: string, {
    region,
    orgId,
    apiGatewayUrl,
    deploymentBucket,
    cloudFront,
    auth,
    deploymentSourceBucketName,
    deploymentSourcePath,
    assetCode,
    solutionVersion,
    stackId,
    sendAnonymousData
  }: WebUIDeployerProps) {
    super(scope, id);

    const deploymentSourceBucket = Bucket.fromBucketAttributes(this, 'SolutionRegionalBucket', {
      bucketName: deploymentSourceBucketName + '-' + region
    });

    const webuiAmplifyConfig = {
      API: {
        endpoints: [
          {
            name: "AccountAssessmentApi",
            endpoint: apiGatewayUrl
          }
        ]
      },
      loggingLevel: 'INFO',
      Auth: {
        region: region,
        userPoolId: auth.userPool.userPoolId,
        userPoolWebClientId: auth.userPoolClient.userPoolClientId,
        mandatorySignIn: true,
        oauth: {
          domain: auth.oauthDomain,
          scope: ["openid", "profile", "email", "aws.cognito.signin.user.admin", "account-assessment-api/api"],
          redirectSignIn: `https://${cloudFront.distributionDomainName}/`,
          redirectSignOut: `https://${cloudFront.distributionDomainName}/`,
          responseType: "code",
          clientId: auth.userPoolClient.userPoolClientId,
        }
      },
      OrgId: orgId
    };
    const webUiDeploymentConfig = {
      SrcBucket: deploymentSourceBucket.bucketName,
      SrcPath: deploymentSourcePath, // Path within the SrcBucket that holds the files to copy
      WebUIBucket: deploymentBucket.bucketName,
      awsExports: webuiAmplifyConfig
    };

    const webUIDeploymentFunction = new lambda.Function(this, 'DeployWebUI', {
      runtime: Runtime.PYTHON_3_12,
      tracing: lambda.Tracing.ACTIVE,
      code: assetCode,
      handler: 'deploy_webui/deploy_webui.lambda_handler',
      timeout: cdk.Duration.minutes(5),
      environment: {
        LOG_LEVEL: 'INFO',
        CONFIG: JSON.stringify(webUiDeploymentConfig),
        POWERTOOLS_SERVICE_NAME: 'DeployWebUI',
        SOLUTION_VERSION: solutionVersion,
        STACK_ID: stackId,
        SEND_ANONYMOUS_DATA: sendAnonymousData
      }
    });
    deploymentBucket.grantPut(webUIDeploymentFunction);
    deploymentSourceBucket.grantRead(webUIDeploymentFunction);

    new CustomResource(this, 'WebUIDeploymentResource', {
      serviceToken: webUIDeploymentFunction.functionArn,
      properties:{
        SolutionVersion: solutionVersion,
      }
    });
  }

}
