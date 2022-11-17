// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {ASSET_PARAMETERS_REGEX} from "./asset-parameters-regex";
import {CfnTemplate} from "../model/CfnTemplate";

/**
 * Clean up "parameters" section of the template by removing AssetParameter-style fields that would have been used to specify Lambda source code properties.
 * This allows solution-specific parameters to be highlighted and removes unnecessary clutter.
 */
export function removeAssetParametersFromTemplate(template: CfnTemplate) {
  const parameters = template.Parameters || {};
  const assetParameters = Object.keys(parameters).filter(
    parameterName => parameterName.search(ASSET_PARAMETERS_REGEX) > -1
  );
  assetParameters.forEach(parameterName => {
    template.Parameters[parameterName] = undefined;
  });
}