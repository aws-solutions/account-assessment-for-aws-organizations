# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.3] - 2025-08-04

### Changed

- CDK and aws-cdk-lib version bump
- Updated TTL for Policy DynamoDB records to 1 day

### Security

- Enhanced security in metrics collection by preventing .netrc credential leakage
- Mitigated [CVE-2024-47081, CVE-2025-27789, CVE-2025-50181, CVE-2025-50182, CVE-2025-5889, CVE-2025-7783]

## [1.1.2] - 2025-05-19

### Added

- Input validation for Cfn parameter "Deployment Namespace"
- Point in time recovery to DynamoDB tables

### Fixed

- Stack deletion no longer fails if Cognito User Pool has been deleted before
- StepFunction no longer fails when scanning large numbers of accounts due to service limit inb step output size

### Removed

- "Delete Job" feature
- AppRegistry integration

### Changed

- Updated dependencies to address setuptools CVE-2025-47273

## [1.1.1] - 2025-02-10

### Changed

- Update vitest version to v3.0.5 to mitigate [CVE-2025-24964](https://nvd.nist.gov/vuln/detail/CVE-2025-24964)

## [1.1.0] - 2025-01-27

### Added

- Daily policy scan via EventBridge Rule / Step Function that records all found policies in DynamoDB
- PolicyExplorer page on the UI
- Ability to export all result tables as .csv
- Support for policy scans in AWS services: AWS RAM, EventBridge Schemas, AWS Systems Manager Incident Manager Contacts,
  Redshift, ACM-PCA and Lex v2
- Support for Service Control Policies

### Changed

- Deprecated Resource Based Policy module in favor of Policy Explorer. Data from previous Resource Based Policy scans
  can still be viewed, but cannot start new scans.
- Upgraded Amplify library from v5 to v6
- Upgraded mock-service-worker library from v1 to v2
- Upgraded from create-react-app to vite

### Fixed

- Make handling of 'content-type' request header case-insensitive to be more resilient to API Gateway service changes
- API error responses are now displayed on the UI properly, no longer disguised as CORS problems

### Removed

- ApplicationInsightsConfiguration due to race condition that caused intermittent deployment failures. Customer can
  still set up ApplicationInsights through AWS Console if desired.

## [1.0.16] - 2024-11-27

### Changed

- Updated dependencies to address cross-spawn CVE-2024-21538

## [1.0.16] - 2024-11-27

### Changed

- Updated dependencies to address cross-spawn CVE-2024-21538

## [1.0.15] - 2024-10-23

### Changed

- Updated dependencies to mitigate CVE-2024-21536
- Add poetry.lock to pin dependency versions for Python code
- Adapt build scripts to use Poetry for dependency management

## [1.0.14] - 2024-10-15

### Changed

- Remove dependencies `bootstrap` and `datefns`
- Allow backend to accept uppercase http headers, to prevent errors when receiving uppercase `Content-type`
- Replace pip3/requirements.txt dependency management with Poetry

### Added

- Add poetry.lock file to support reproducible builds, improve vulnerability scanning

## [1.0.13] - 2024-09-24

- Upgrade `rollup` to mitigate [CVE-2024-47068](https://nvd.nist.gov/vuln/detail/CVE-2024-47068)

## [1.0.12] - 2024-09-17

- `path-to-regexp` to mitigate [CVE-2024-45296](https://avd.aquasec.com/nvd/cve-2024-45296)

## [1.0.11] - 2024-09-12

### Fixed

- Added support for keys `aws:SourceOrgID`, `aws:SourceOrgPaths` in policy conditions

### Changed

- `moto` from v4.x to v5.x for python unit tests
- `micromatch` to mitigate [CVE-2024-4067](https://avd.aquasec.com/nvd/cve-2024-4067)
- `webpack` to mitigate [CVE-2024-43788](https://avd.aquasec.com/nvd/cve-2024-43788)
- `express` to mitigate [CVE-2024-43796](https://avd.aquasec.com/nvd/cve-2024-43796)
- `send` to mitigate [CVE-2024-43799](https://avd.aquasec.com/nvd/cve-2024-43799)
- `serve-static` to mitigate [CVE-2024-43800](https://avd.aquasec.com/nvd/cve-2024-43800)
- `path-to-regexp` to mitigate [CVE-2024-45296](https://avd.aquasec.com/nvd/cve-2024-45296)
- `body-parser` to mitigate [CVE-2024-45590](https://avd.aquasec.com/nvd/cve-2024-45590)

## [1.0.10] - 2024-08-13

- Upgrade `axios` to mitigate [CVE-2024-39338](https://nvd.nist.gov/vuln/detail/CVE-2024-39338)

## [1.0.9] - 2024-08-01

### Security

- Upgrade `fast-xml-parser` to mitigate [CVE-2024-41818](https://nvd.nist.gov/vuln/detail/CVE-2024-41818)

### Fixed

- When scan fails for a certain S3 bucket, the solution will no longer fail the scan for all S3 buckets in the account.
  The failed buckets will be reported as individual failures with bucket name in on the solution UI, while scan results
  for all other buckets will be reported successfully.

## [1.0.8] - 2024-06-18

### Fixed

- Updated package versions to resolve security vulnerabilities.

## [1.0.7] - 2024-06-07

### Fixed

- Updated package versions to resolve security vulnerabilities.

## [1.0.6] - 2024-03-29

### Fixed

- Updated package versions to resolve security vulnerabilities.
- Pinned boto3 and botocore versions to ~1.34.0

## [1.0.5] - 2023-10-29

### Fixed

- Updated package versions to resolve security vulnerabilities.

## [1.0.4] - 2023-04-17

### Changed

- Mitigated impact caused by new default settings for S3 Object Ownership (ACLs disabled) for all new S3 buckets.

## [1.0.3] - 2023-03-31

### Changed

- Support scanning more than five specified OpenSearch Service domains. Fixed [#7](https://github.com/aws-solutions/account-assessment-for-aws-organizations/issues/7)
- Support scanning S3 bucket policies in the Opt-In regions.
- AppRegistry Attribute Group name with a unique string.

## [1.0.2] - 2023-02-16

### Added

- Optional Multi-factor authentication (MFA) for Cognito User Pool

### Changed

- Shortened the role name in OrgManagementStack to avoid name length constraints in some
  regions. [#3](https://github.com/aws-solutions/account-assessment-for-aws-organizations/issues/3)
- Encryption of DynamoDB tables from AWS owned to AWS managed key. Allows customers to view key metadata and audit key
  use in AWS CloudTrail logs.
- Increase Lambda function memory size to scan large number of accounts in AWS Organizations
- Ignore deleted CloudFormation stacks in the Resource-based policy scan.
- Fix typo to process next marker when listing IoT policies.

## [1.0.1] - 2022-01-11

### Changed

- Updated 3rd party library versions
- Mitigated [vulnerability in py library](https://www.cvedetails.com/cve/CVE-2022-42969/) by updating pytest version

## [1.0.0] - 2022-11-14

### Added

- All files, initial version
