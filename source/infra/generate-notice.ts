// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * To generate a meaningful NOTICE.txt, make sure all 3rd party libraries that are distributed with the solution package
 * (all production dependencies, not devDependencies) are installed before running this script.
 */
import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

const HEADER = `account-assessment-for-aws-organizations
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
Licensed under the Apache License Version 2.0 (the "License"). You may not use this file except
in compliance with the License. A copy of the License is located at http://www.apache.org/licenses/
or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the
specific language governing permissions and limitations under the License.

**********************
THIRD PARTY COMPONENTS
**********************
This software includes third party software subject to the following copyrights:

`;

const PROJECT_NAME = 'account-assessment-for-aws-organizations';

function getPythonDependencies(): string[] {
    console.log('⏳ Getting Python dependencies from lambda folder...');
    try {
        console.log('ℹ️  Running pip list command...');
        const output = execSync('pip list --format=json', {
            cwd: path.join(process.cwd(), 'lambda'),
            encoding: 'utf-8'
        });

        const dependencies: string[] = [];
        const pipPackages = JSON.parse(output);
        const totalDeps = pipPackages.length;

        console.log(`ℹ️  Found ${totalDeps} Python dependencies to process`);

        for (let i = 0; i < pipPackages.length; i++) {
            const pkg = pipPackages[i];
            const name = pkg.name;

            if (name && !name.startsWith(PROJECT_NAME)) {
                try {
                    process.stdout.write(`\r⏳ Processing Python dependency ${i + 1}/${totalDeps}: ${name}`);

                    // Get package metadata using pip show
                    const metadataOutput = execSync(`pip show "${name}"`, {
                        cwd: path.join(process.cwd(), 'lambda'),
                        encoding: 'utf-8',
                        stdio: ['pipe', 'pipe', 'ignore'] // Suppress stderr
                    });

                    const lines = metadataOutput.split('\n');
                    let license = 'UNKNOWN';
                    for (const line of lines) {
                        if (line.toLowerCase().startsWith('license:')) {
                            license = line.split(':')[1]?.trim() || 'UNKNOWN';
                            break;
                        }
                    }

                    if (license && license !== 'UNKNOWN') {
                        dependencies.push(`${name.padEnd(25)} ${license}`);
                    } else {
                        process.stdout.write(`\n⚠️  No license found for ${name}\n`);
                    }
                } catch (e) {
                    process.stdout.write(`\n❌ Error getting license for ${name}\n`);
                }
            }
        }
        console.log('\n✅ Finished processing Python dependencies');
        console.log(`ℹ️  Total Python dependencies processed: ${dependencies.length}`);
        return dependencies;
    } catch (error) {
        console.error('❌ Error reading Python dependencies:', error);
        return [];
    }
}


function getNodeDependencies(directory: string): string[] {
    console.log(`⏳ Getting Node.js dependencies for ${directory}...`);
    try {
        const output = execSync('license-checker --json', {
            cwd: path.join(process.cwd(), directory),
            encoding: 'utf-8'
        });

        const deps = JSON.parse(output);
        return Object.entries(deps)
            .filter(([key]) => {
                const [name] = key.split('@');
                return name && !name.startsWith(PROJECT_NAME);
            })
            .map(([key, value]: [string, any]) => {
                const [name] = key.split('@');
                return `${name.padEnd(25)} ${value.licenses}`;
            });
    } catch (error) {
        console.error(`❌ Error reading Node.js dependencies for ${directory}:`, error);
        return [];
    }
}

function generateNotice() {
    console.log('⏳ Starting NOTICE.txt generation...');
    let content = HEADER;

    // Python dependencies
    const pythonDeps = getPythonDependencies();
    if (pythonDeps.length > 0) {
        console.log(`ℹ️  Adding ${pythonDeps.length} Python dependencies to NOTICE.txt`);
        content += 'Python Packages:\n';
        content += '=================\n';
        content += pythonDeps.sort().map(dep => ` ${dep}`).join('\n') + '\n\n';
    } else {
        console.log('⚠️  No Python dependencies found to add to NOTICE.txt');
    }

    // Node.js dependencies
    const infraDeps = getNodeDependencies('infra');
    const webuiDeps = getNodeDependencies('webui');
    const nodeDeps = new Set([...infraDeps, ...webuiDeps]);

    if (nodeDeps.size > 0) {
        console.log(`ℹ️  Adding ${nodeDeps.size} Node.js dependencies to NOTICE.txt`);
        content += 'Node.js Packages:\n';
        content += '==================\n';
        content += Array.from(nodeDeps).sort().map(dep => ` ${dep}`).join('\n') + '\n';
    } else {
        console.log('⚠️  No Node.js dependencies found to add to NOTICE.txt');
    }

    // Write to file
    try {
        fs.writeFileSync('../NOTICE.txt', content);
        console.log('✅ Successfully generated NOTICE.txt');
        console.log('ℹ️  Content preview:');
        console.log(content.slice(0, 500) + '...');
    } catch (error) {
        console.error('❌ Error writing NOTICE.txt:', error);
    }
}

console.log('ℹ️  Starting dependency license collection...');
generateNotice();

