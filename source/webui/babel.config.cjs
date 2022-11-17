// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

module.exports = {
    ignore: [/node_modules\/?!@cloudscape-design\/components-react/],
    presets: [
        '@babel/preset-env',
        ['@babel/preset-react', {
            "runtime": "automatic"
        }],
        '@babel/preset-typescript'
    ]
};