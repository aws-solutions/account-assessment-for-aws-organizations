// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// This regex is used to find properties in the cf templates
// that are cdk-generated references to S3 assets (e.g. lambda code)
export const ASSET_PARAMETERS_REGEX = /\w{0,64}AssetParameters/g;
