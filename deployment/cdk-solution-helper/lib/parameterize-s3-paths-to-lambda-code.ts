// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {CfnTemplate} from "../model/CfnTemplate";

const LAMBDA_ARTIFACT_NAME = `lambda`;

export function parameterizeLambdaS3References(template: CfnTemplate) {
  const lambdaFunctionNames = getResourceNamesOfType(template, "AWS::Lambda::Function");

  lambdaFunctionNames.forEach(lambdaFunction => {
    const fn = template.Resources[lambdaFunction];
    if (fn.Properties.Code.hasOwnProperty('S3Bucket')) {
      // Set the S3 key reference
      fn.Properties.Code.S3Key = `%%SOLUTION_NAME%%/%%VERSION%%/${LAMBDA_ARTIFACT_NAME}.zip`;
      // Set the S3 bucket reference
      fn.Properties.Code.S3Bucket = {
        'Fn::Sub': '%%BUCKET_NAME%%-${AWS::Region}'
      };
    }
  });
}

function getResourceNamesOfType(template: any, resourceType: string): string[] {
  const resources = template.Resources || {};
  return Object.keys(resources).filter(key =>
    resources[key].Type === resourceType
  );
}