# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.16] - 2024-11-27

### Changed

- Updated dependencies to address cross-spawn CVE-2024-21538

## [1.0.15] - 2024-10

### Changed

- Updated dependencies to mitigate CVE-2024-21536
- Add poetry.lock to pin dependency versions for Python code
- Adapt build scripts to use Poetry for dependency management

## [1.0.14] - 2024-10

### Changed

- Remove dependencies `bootstrap` and `datefns`
- Allow backend to accept uppercase http headers, to prevent errors when receiving uppercase `Content-type`
- Replace pip3/requirements.txt dependency management with Poetry

### Added

- Add poetry.lock file to support reproducible builds, improve vulnerability scanning

## [1.0.13] - 2024-9

- Upgrade `rollup` to mitigate [CVE-2024-47068](https://nvd.nist.gov/vuln/detail/CVE-2024-47068)

## [1.0.12] - 2024-9

- `path-to-regexp` to mitigate [CVE-2024-45296](https://avd.aquasec.com/nvd/cve-2024-45296)

## [1.0.11] - 2024-9

### Fixed

- Added support for keys `aws:SourceOrgID`, `aws:SourceOrgPaths` in policy conditions

### Updated dependencies

- `moto` from v4.x to v5.x for python unit tests
- `micromatch` to mitigate [CVE-2024-4067](https://avd.aquasec.com/nvd/cve-2024-4067)
- `webpack` to mitigate [CVE-2024-43788](https://avd.aquasec.com/nvd/cve-2024-43788)
- `express` to mitigate [CVE-2024-43796](https://avd.aquasec.com/nvd/cve-2024-43796)
- `send` to mitigate [CVE-2024-43799 ](https://avd.aquasec.com/nvd/cve-2024-43799)
- `serve-static` to mitigate [CVE-2024-43800](https://avd.aquasec.com/nvd/cve-2024-43800)
- `path-to-regexp` to mitigate [CVE-2024-45296](https://avd.aquasec.com/nvd/cve-2024-45296)
- `body-parser` to mitigate [CVE-2024-45590](https://avd.aquasec.com/nvd/cve-2024-45590)

## [1.0.10] - 2024-8

- Upgrade `axios` to mitigate [CVE-2024-39338](https://nvd.nist.gov/vuln/detail/CVE-2024-39338)

## [1.0.9] - 2024-08

### Security

- Upgrade `fast-xml-parser` to mitigate [CVE-2024-41818](https://nvd.nist.gov/vuln/detail/CVE-2024-41818)

### Fixed

- When scan fails for a certain S3 bucket, the solution will no longer fail the scan for all S3 buckets in the account.
  The failed buckets will be reported as individual failures with bucket name in on the solution UI, while scan results
  for all other buckets will be reported successfully.

## [1.0.8] - 2024-06

### Fixed

- Updated package versions to resolve security vulnerabilities.

## [1.0.7] - 2024-06

### Fixed

- Updated package versions to resolve security vulnerabilities.

## [1.0.6] - 2024-03

### Fixed

- Updated package versions to resolve security vulnerabilities.
- Pinned boto3 and botocore versions to ~1.34.0

## [1.0.5] - 2023-10

### Fixed

- Updated package versions to resolve security vulnerabilities.

## [1.0.4] - 2023-04

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
