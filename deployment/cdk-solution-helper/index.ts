// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0


import * as fs from 'fs';
import * as path from "path";
import {removeAssetParametersFromTemplate} from "./lib/remove-asset-parameters-from-template";
import {parameterizeLambdaS3References,} from "./lib/parameterize-s3-paths-to-lambda-code";
import {CfnTemplate} from "./model/CfnTemplate";

const globalS3AssetsDir = '../global-s3-assets';
const globalS3templateFileNames = fs.readdirSync(globalS3AssetsDir).filter(it => it.endsWith('.template'));
console.log(`Processing template files: ${globalS3templateFileNames}`);

// For each template in global_s3_assets ...
globalS3templateFileNames.forEach(templateFileName => {
    // Import and parse template file
    const template = readAndParseTemplate(templateFileName);

    // Clean-up Lambda function code dependencies
    parameterizeLambdaS3References(template);

    // Clean-up parameters section
    removeAssetParametersFromTemplate(template);

    // Output modified template file
    writeModifiedTemplate(template, templateFileName);
    console.log(`Processed: ${templateFileName}`);
});

function readAndParseTemplate(file: string): CfnTemplate {
    const rawTemplate: string = fs.readFileSync(
      path.join(globalS3AssetsDir, file),
      {encoding: 'utf-8'}
    );
    return JSON.parse(rawTemplate) as CfnTemplate;
}

function writeModifiedTemplate(template: any, fileName: string) {
    const modifiedTemplateJson = JSON.stringify(template, null, 2);
    fs.writeFileSync(`${globalS3AssetsDir}/${fileName}`, modifiedTemplateJson);
}
