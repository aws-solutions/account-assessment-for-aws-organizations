# Guidance for Account Assessment for AWS Organizations

Guidance for Account Assessment for AWS Organizations provides centralized visibility into dependencies across an
AWS Organization. It discovers trusted access enabled services, delegated administrator accounts, and identity-based,
resource-based, and service control policies across accounts and AWS Regions.

**[🚀 Guidance landing page](https://aws.amazon.com/solutions/implementations/account-assessment-for-aws-organizations)**

_Note:_ For any relevant information outside the scope of this README, refer to the Guidance landing page and
implementation guide.

## Table of contents

- [Guidance overview](#guidance-overview)
- [Architecture](#architecture)
- [Deploy with AWS CDK](#deploy-with-aws-cdk)
- [Customization](#customization)
  - [Setup](#setup)
  - [File Structure](#file-structure)
  - [Unit Test](#unit-test)
  - [Faster development cycles](#faster-development-cycles)
- [Data collection](#data-collection)
- [License](#License)

## Guidance overview

This Guidance provides a web interface for on-demand scans of delegated administrator accounts and trusted access
enabled services, plus daily automated scans of identity-based, resource-based, and service control policies across
active accounts and AWS Regions.

## Architecture

The default deployment of this Guidance creates the following infrastructure in your accounts.

<img src="./docs/architecture.png" alt="architecture diagram">

## Deploy with AWS CDK

These steps deploy the Guidance from source with AWS CDK. The deployment uses three stacks:

- A hub stack in a dedicated hub account.
- An organization management stack in the AWS Organizations management account.
- A spoke stack in every account that you want to assess.

Before deploying:

- Install the AWS CLI, Python 3.12, Node.js 22+, npm, and Poetry v2 with the export plugin. The Lambda build must use
  Python 3.12; verify that both `python3` and `pip3` resolve to that version.
- Configure AWS CLI profiles for the hub, organization management, and spoke accounts. Configure all profiles to use
  the same AWS Region.
- Ensure that the credentials used for each profile have permission to deploy the applicable AWS CDK stack. The hub
  credentials must also have permission to bootstrap the account.

Verify the local build tools:

```shell
python3 --version
pip3 --version
node --version
poetry --version

poetry self add poetry-plugin-export
poetry export --help
```

If the Poetry installation cannot install self plugins, use an isolated Python 3.12 environment for the build:

```shell
python3.12 -m venv /tmp/account-assessment-build
source /tmp/account-assessment-build/bin/activate
pip install "poetry>=2,<3" poetry-plugin-export
```

Clone the repository and configure the deployment values:

```shell
git clone https://github.com/aws-solutions-library-samples/account-assessment-for-aws-organizations.git
cd account-assessment-for-aws-organizations

export AWS_REGION=us-east-2
export AWS_DEFAULT_REGION="$AWS_REGION"
export PROFILE_HUB=hub-profile
export PROFILE_ORG_MGMT=org-management-profile
export PROFILE_SPOKE=spoke-profile

export HUB_ACCOUNT_ID=444455556666
export MANAGEMENT_ACCOUNT_ID=111122223333

export DIST_OUTPUT_BUCKET="account-assessment-staging-${HUB_ACCOUNT_ID}"
export SOLUTION_ID=SO0217
export SOLUTION_NAME="Account Assessment for AWS Organizations"
export SOLUTION_TRADEMARKEDNAME=account-assessment-for-aws-organizations
export SOLUTION_VERSION=v1.1.13
export ASSET_BUCKET_NAME="${DIST_OUTPUT_BUCKET}-${AWS_REGION}"
```

Confirm that each profile targets the expected account before creating resources:

```shell
aws sts get-caller-identity --profile "$PROFILE_HUB"
aws sts get-caller-identity --profile "$PROFILE_ORG_MGMT"
aws sts get-caller-identity --profile "$PROFILE_SPOKE"
```

In the organization management account, enable resource sharing with AWS Organizations in AWS Resource Access
Manager. This enables trusted access for AWS RAM across the organization and should be approved by the organization
administrator:

```shell
aws ram enable-sharing-with-aws-organization \
  --region "$AWS_REGION" \
  --profile "$PROFILE_ORG_MGMT"

aws organizations list-aws-service-access-for-organization \
  --query "EnabledServicePrincipals[?ServicePrincipal=='ram.amazonaws.com'].ServicePrincipal" \
  --output text \
  --profile "$PROFILE_ORG_MGMT"
```

The asset bucket must be in the hub account. Create it, build the Lambda and Web UI assets, and upload the Web UI:

```shell
aws s3 mb "s3://${ASSET_BUCKET_NAME}" \
  --region "$AWS_REGION" \
  --profile "$PROFILE_HUB"

cd deployment
chmod +x build-s3-dist.sh build-lambdas.sh
./build-s3-dist.sh "$DIST_OUTPUT_BUCKET" "$SOLUTION_VERSION"
cd ..

aws s3 cp deployment/regional-s3-assets/webui/ \
  "s3://${ASSET_BUCKET_NAME}/${SOLUTION_TRADEMARKEDNAME}/${SOLUTION_VERSION}/webui/" \
  --recursive \
  --profile "$PROFILE_HUB"
```

Install the CDK project dependencies, compile the CDK application, and bootstrap the hub account and Region:

```shell
cd source/infra
npm ci
npm run build

npm run cdk -- bootstrap "aws://${HUB_ACCOUNT_ID}/${AWS_REGION}" --profile "$PROFILE_HUB"
```

The organization management and spoke stacks do not currently contain file assets, so they can be deployed without
bootstrapping when the active credentials can deploy CloudFormation directly. Bootstrap those accounts too if your
environment requires the CDK deployment roles.

Choose the stack parameter values:

- `DeploymentNamespace`: A unique 3–10 character value shared by all three stacks.
- `UserEmail`: The email address for the initial Amazon Cognito user.
- `AllowListedIPRanges`: Comma-separated CIDR ranges allowed to access the API.
- `OrganizationID`: The AWS Organizations ID, for example `o-example12345`.
- `ManagementAccountId`: The account ID of the AWS Organizations management account.
- `HubAccountId`: The account ID where the hub stack is deployed.

Set the stack parameter values:

```shell
export DEPLOYMENT_NAMESPACE=acct-scan
export USER_EMAIL=admin@example.com
export ALLOW_LISTED_IP_RANGES="203.0.113.10/32"
export ORGANIZATION_ID=o-example12345
```

Replace the example email and CIDR with reachable, trusted values. The email receives the initial Amazon Cognito
invitation. Avoid the template's internet-wide allow-list default unless that exposure is intentional.

Review the proposed changes before deployment:

```shell
npm run cdk -- diff account-assessment-for-aws-organizations-hub \
  --parameters DeploymentNamespace="$DEPLOYMENT_NAMESPACE" \
  --parameters UserEmail="$USER_EMAIL" \
  --parameters AllowListedIPRanges="$ALLOW_LISTED_IP_RANGES" \
  --parameters OrganizationID="$ORGANIZATION_ID" \
  --parameters ManagementAccountId="$MANAGEMENT_ACCOUNT_ID" \
  --region "$AWS_REGION" \
  --profile "$PROFILE_HUB"

npm run cdk -- diff account-assessment-for-aws-organizations-org-management \
  --parameters DeploymentNamespace="$DEPLOYMENT_NAMESPACE" \
  --parameters HubAccountId="$HUB_ACCOUNT_ID" \
  --region "$AWS_REGION" \
  --profile "$PROFILE_ORG_MGMT"

npm run cdk -- diff account-assessment-for-aws-organizations-spoke \
  --parameters DeploymentNamespace="$DEPLOYMENT_NAMESPACE" \
  --parameters HubAccountId="$HUB_ACCOUNT_ID" \
  --region "$AWS_REGION" \
  --profile "$PROFILE_SPOKE"
```

Run CDK commands sequentially when they use the default `cdk.out` directory. Parallel commands must each use a
different `--output` directory.

Deploy the stacks:

```shell
npm run deploy -- \
  --parameters DeploymentNamespace="$DEPLOYMENT_NAMESPACE" \
  --parameters UserEmail="$USER_EMAIL" \
  --parameters AllowListedIPRanges="$ALLOW_LISTED_IP_RANGES" \
  --parameters OrganizationID="$ORGANIZATION_ID" \
  --parameters ManagementAccountId="$MANAGEMENT_ACCOUNT_ID" \
  --region "$AWS_REGION" \
  --profile "$PROFILE_HUB"

npm run deployOrgMgmt -- \
  --parameters DeploymentNamespace="$DEPLOYMENT_NAMESPACE" \
  --parameters HubAccountId="$HUB_ACCOUNT_ID" \
  --region "$AWS_REGION" \
  --profile "$PROFILE_ORG_MGMT"

npm run deploySpoke -- \
  --parameters DeploymentNamespace="$DEPLOYMENT_NAMESPACE" \
  --parameters HubAccountId="$HUB_ACCOUNT_ID" \
  --region "$AWS_REGION" \
  --profile "$PROFILE_SPOKE"
```

Repeat the spoke diff and deployment commands for every account that the Guidance should assess. Use a profile that
targets the account, or assume a deployment role such as `AWSControlTowerExecution` where your governance model
permits it.

Return to the repository root when the deployment is complete:

```shell
cd ../..
```

***

## Customization

### Setup

- Python 3.12 with pip
- AWS CDK 2.1021.0+
- Node.js 22+ with npm
- Poetry v2 with plugin to export

Clone the repository and make the desired code changes.

```shell
git clone https://github.com/aws-solutions-library-samples/account-assessment-for-aws-organizations.git
```

_Note: Following steps have been tested under above pre-requisites_

### File Structure

```
├── deployment/                             - contains build scripts, deployment templates, and dist folders for staging assets.
  ├── cdk-solution-helper/                  - helper function for converting CDK output to a format compatible with the AWS Solutions pipelines.
  ├── build-open-source-dist.sh             - builds the open source package with cleaned assets and builds a .zip file in the /open-source folder for distribution to GitHub
  ├── build-s3-dist.sh                      - builds the Guidance and copies artifacts to the appropriate /global-s3-assets or /regional-s3-assets folders.
  ├── build-lambdas.sh                      - builds and packages the lambda code only
├── source/   
  ├── account-assessment-solution.ts        - the CDK app that wraps the Guidance.
  ├── infra/                                - the source code for the infrastructure-as-code AWS CDK project
     ├── bin
       └──  account-assessment-solution.ts     - the CDK app for the Guidance.
     ├── lib
       ├── account-assessment-hub-stack.ts    - the hub CDK stack.
       ├── account-assessment-spoke-stack.ts  - the spoke CDK stack.
       ├──org-management-account-stack.ts     - the AWS Organizations Management CDK stack.
       └── components                         - hub stack resources grouped into constructs for better maintainability 
         ├── api.ts                            - resources related to API Gateway
         ├── cognito-authenticator.ts          - resources related to authentication
         ├── job-history-component.ts          - DynamoDB table and Lambda functions related to the job management microservice
         ├── resource-based-policy-component.ts - Lambda functions related to the resouce based policy microservice
         ├── resource-based-policy-state-machine.ts - custom resource to deploy the Guidance Web UI to S3
         ├── simple-assessment-component.ts    - generic set of DynamoDB table and Lambda functions for all microservices.
         ├── web-ui-deployer.ts                - custom resource to deploy the Guidance Web UI to S3
         └── web-ui-hosting.ts                 - resources to host the web ui in S3
     └── test/
        └── __snapshots__/
├── cdk-solution-test.ts                    - example unit and snapshot tests for CDK project.
  ├── cdk.json                              - config file for CDK.
  ├── package.json                          - package file for the CDK project.
  ├── README.md                             - doc file for the CDK project.
  ├── lambda/                               - the source code for the Guidance's Lambda functions
    ├── requirements.txt
    ├── testing_requirements.txt            - python test dependency file
    ├── assessment_runner/                  - job management microservice
    ├── aws/
    ├── services                            - low-level clients to interact with AWS Services
        └── utils/
    ├── delegated_admins/                   - delegated admin scan microservice
    ├── deploy_webui/                       - Lambda-backed custom resource to deploy the Guidance Web UI to S3
    ├── resource_based_policy/              - IAM policies scan microservice
        ├── step_functions_lambda/
        └── supported_configuration/
    ├── tests/
    ├── trusted_access_enabled_services/    - Trusted AWS Services scan microservice
    └── utils/
  ├── webui                                 - React app that serves as the user interface for this Guidance
  ├── run-all-tests.sh                      - runs all tests within the /source folder. Referenced in the buildspec and build scripts.
├── .gitignore
├── .viperlightignore                       - Viperlight scan ignore configuration  (accepts file, path, or line item).
├── .viperlightrc                           - Viperlight scan configuration.
├── buildspec.yml                           - main build specification for CodeBuild to perform builds and execute unit tests.
├── CHANGELOG.md                            - records changes by version for release notes.
├── CODE_OF_CONDUCT.md                      - standardized open source code of conduct.
├── CONTRIBUTING.md                         - standardized open source contribution guidance.
├── LICENSE.txt                             - contains the Apache 2.0 license.
├── NOTICE.txt                              - contains references to third-party libraries.
├── README.md                               - provides Guidance documentation.
```

### Unit Test

Run unit tests to make sure added customization passes the tests.

```
cd ./source
chmod +x ./run-all-tests.sh
./run-all-tests.sh
cd ..
```

_✅ Ensure all unit tests pass. Review the generated coverage report_

### Faster development cycles

Once you have built and deployed the complete Guidance once, you may want to shorten the cycle times for iterative
development.

#### Frontend development

- Download the file `aws-exports-generated.json` from your WebUIHostingBucket that was created during the first
  deployment.
- Place the file in `/source/webui/public`
- Replace the generated values of the following properties in the file to point to localhost:

```      
"redirectSignIn": "http://localhost:3000/",
"redirectSignOut": "http://localhost:3000/",
```

Start the Web UI React app locally. It will use Amazon Cognito and Amazon API Gateway in your hub account as the
backend.

```shell
cd ./source/webui
npm run start
```

#### Backend development

When you change only the Lambda function code in `source/lambda`, package and deploy it without rebuilding the Web UI:

```shell
cd ./source/infra
npm run buildLambdaAndDeploy -- \
  --parameters DeploymentNamespace="$DEPLOYMENT_NAMESPACE" \
  --parameters UserEmail="$USER_EMAIL" \
  --parameters AllowListedIPRanges="$ALLOW_LISTED_IP_RANGES" \
  --parameters OrganizationID="$ORGANIZATION_ID" \
  --parameters ManagementAccountId="$MANAGEMENT_ACCOUNT_ID" \
  --region "$AWS_REGION" \
  --profile "$PROFILE_HUB"
cd ../..
```

This will replace the file `deployment/regional-s3-assets/lambda.zip` from your initial build with a new package of your
modified source code and its dependencies, retaining `deployment/regional-s3-assets/webui` from the initial build.

#### CDK development

When you change only the CDK app, deploy the hub stack without rebuilding the Web UI or Lambda package:

```shell
cd ./source/infra
npm run deploy -- \
  --parameters DeploymentNamespace="$DEPLOYMENT_NAMESPACE" \
  --parameters UserEmail="$USER_EMAIL" \
  --parameters AllowListedIPRanges="$ALLOW_LISTED_IP_RANGES" \
  --parameters OrganizationID="$ORGANIZATION_ID" \
  --parameters ManagementAccountId="$MANAGEMENT_ACCOUNT_ID" \
  --region "$AWS_REGION" \
  --profile "$PROFILE_HUB"
cd ../..
```

This updates the hub stack with the changed resources but uses the unchanged Web UI and Lambda code in
`deployment/regional-s3-assets` from the initial build.

***

## Data Collection

This Guidance sends operational metrics to AWS (the “Data”) about the use of this Guidance. We use this Data to better
understand how customers use this Guidance and related services and products. AWS’s collection of this Data is subject
to the [AWS Privacy Notice](https://aws.amazon.com/privacy/).

***

## License

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License Version 2.0 (the "License"). You may not use this file except in compliance with the
License. A copy of the License is located at

    http://www.apache.org/licenses/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and
limitations under the License.
