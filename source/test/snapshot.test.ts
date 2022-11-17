// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import '@aws-cdk/assert/jest';
import {App} from 'aws-cdk-lib';
import {AccountAssessmentHubStack, AccountAssessmentHubStackProps} from "../lib/account-assessment-hub-stack";
import {Template} from "aws-cdk-lib/assertions";
import {existsSync} from "fs";
import {mkdir} from "node:fs";
import {OrgManagementAccountStack} from "../lib/org-management-account-stack";
import {SpokeStack} from "../lib/account-assessment-spoke-stack";

export const props: AccountAssessmentHubStackProps = {
  solutionBucketName: 'solutions',
  solutionId: 'SO0217',
  solutionName: 'account-assessment-for-aws-organizations',
  solutionProvider: 'AWS Solutions',
  solutionTradeMarkName: 'account-assessment-for-aws-organizations',
  solutionVersion: 'v1.0.0'
};

/*
 * Regression test.
 * Compares the synthesized cfn template from the cdk project with the snapshot in git.
 *
 * Only update the snapshot after making sure that the differences are intended. (Deployment and extensive manual testing)
 */
test('hub stack synth doesnt crash', () => {
  // GIVEN
  const app = new App();

  const uiBuildOutputDir = `${__dirname}/../webui/build`;
  if (!existsSync(uiBuildOutputDir)) {
    mkdir(uiBuildOutputDir, {recursive: true}, (err) => {
      if (err) throw err;
    });
  }

  // WHEN
  const stack = new AccountAssessmentHubStack(
    app,
    'AccountAssessment-HubStack',
    props
  );
  const template = Template.fromStack(stack);

  // THEN
  expect(template).toMatchSnapshot();
});

test('org management stack synth doesnt crash', () => {
  // GIVEN
  const app = new App();

  // WHEN
  const stack = new OrgManagementAccountStack(
    app,
    'AccountAssessment-OrgMgmtStack',
    props
  );
  const template = Template.fromStack(stack);

  // THEN
  expect(template).toMatchSnapshot();
});

test('spoke stack synth doesnt crash', () => {
  // GIVEN
  const app = new App();

  // WHEN
  const stack = new SpokeStack(
    app,
    'AccountAssessment-SpokeStack',
    props
  );
  const template = Template.fromStack(stack);

  // THEN
  expect(template).toMatchSnapshot();
});
