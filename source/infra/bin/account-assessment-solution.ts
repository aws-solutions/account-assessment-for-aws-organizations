// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as cdk from 'aws-cdk-lib';
import {DefaultStackSynthesizer, IAspect} from 'aws-cdk-lib';
import 'source-map-support/register';
import * as lambda from "aws-cdk-lib/aws-lambda";
import {AccountAssessmentHubStack, AccountAssessmentHubStackProps} from "../lib/account-assessment-hub-stack";
import {OrgManagementAccountStack} from "../lib/org-management-account-stack";
import {SpokeStack} from "../lib/account-assessment-spoke-stack";
import {AppRegister} from "../lib/app-register";
import {IConstruct} from "constructs";
import {CfnPolicy} from "aws-cdk-lib/aws-iam";
import {addCfnSuppressRules} from "@aws-solutions-constructs/core";

function getEnvElement(envVariableName: string): string {
  const value: string | undefined = process.env[envVariableName];
  if (value == undefined) throw new Error(`Missing required environment variable ${envVariableName}`)
  return value;
}

const SOLUTION_VERSION = getEnvElement('SOLUTION_VERSION');
const SOLUTION_NAME = getEnvElement('SOLUTION_NAME');
const SOLUTION_ID = process.env['SOLUTION_ID'] || 'SO0217';
const SOLUTION_BUCKET_NAME = getEnvElement('DIST_OUTPUT_BUCKET');
const SOLUTION_TMN = getEnvElement('SOLUTION_TRADEMARKEDNAME');
const SOLUTION_PROVIDER = 'AWS Solution Development';

let accountAssessmentHubStackProperties: AccountAssessmentHubStackProps = {
  solutionId: SOLUTION_ID,
  solutionTradeMarkName: SOLUTION_TMN,
  solutionProvider: SOLUTION_PROVIDER,
  solutionBucketName: SOLUTION_BUCKET_NAME,
  solutionName: SOLUTION_NAME,
  solutionVersion: SOLUTION_VERSION,
  description: '(' + SOLUTION_ID + ') - The AWS CloudFormation hub template' +
    ' for deployment of the ' + SOLUTION_NAME + ', Version: ' + SOLUTION_VERSION,
  synthesizer: new DefaultStackSynthesizer({
    generateBootstrapVersionRule: false
  })
}

const app = new cdk.App();

const accountAssessmentHubStack = new AccountAssessmentHubStack(
  app,
  'account-assessment-for-aws-organizations-hub',
  accountAssessmentHubStackProperties
);

const orgManagementAccountStack = new OrgManagementAccountStack(
  app,
  'account-assessment-for-aws-organizations-org-management',
  {
    description: '(' + SOLUTION_ID + 'm) - The AWS CloudFormation org management template' +
      ' for deployment of the ' + SOLUTION_NAME + ', Version: ' + SOLUTION_VERSION,
    synthesizer: new DefaultStackSynthesizer({
      generateBootstrapVersionRule: false
    })
  }
);

const spokeStack = new SpokeStack(
  app,
  'account-assessment-for-aws-organizations-spoke',
  {
    description: '(' + SOLUTION_ID + 's) - The AWS CloudFormation spoke template' +
      ' for deployment of the ' + SOLUTION_NAME + ', Version: ' + SOLUTION_VERSION,
    synthesizer: new DefaultStackSynthesizer({
      generateBootstrapVersionRule: false
    })
  }
);

/**
 * Since all lambda functions are traced with xray,
 * and xray:PutTraceSegments requires a policy with resource *,
 * we have to suppress cfn nag warning W12 for every lambda function.
 */
class SuppressCfnNagW12ForLambdaFunctions implements IAspect {
  visit(node: IConstruct): void {
    if (node instanceof lambda.Function) {
      const cfnPolicy = node.node.tryFindChild('ServiceRole')
        ?.node.findChild('DefaultPolicy')
        .node.findChild('Resource') as CfnPolicy;
      cfnPolicy && addCfnSuppressRules(cfnPolicy, [{
        id: 'W12',
        reason: 'Resource * is necessary for xray:PutTraceSegments and xray:PutTelemetryRecords.'
      }]);
    }
  }
}

cdk.Aspects.of(app).add(new SuppressCfnNagW12ForLambdaFunctions());

export const APP_REGISTER = new AppRegister({
  solutionId: SOLUTION_ID,
  solutionName: SOLUTION_NAME.replace(/\s/g, ''),
  solutionDomain: "CloudFoundations",
  solutionVersion: SOLUTION_VERSION,
  appRegistryApplicationName: SOLUTION_NAME.replace(/\s/g, ''),
  applicationType: "AWS-Solutions",
});

APP_REGISTER.applyAppRegistryToStacks(accountAssessmentHubStack, [spokeStack, orgManagementAccountStack], [], accountAssessmentHubStack.appRegisterData);

app.synth();

