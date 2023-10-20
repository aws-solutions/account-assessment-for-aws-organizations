# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.5] - 2023-04

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
