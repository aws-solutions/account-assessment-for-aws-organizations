// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {format} from "date-fns";

const formattedDateTime = (isoDateTime?: string) => {
  if (isoDateTime)
    return format(new Date(isoDateTime), 'yyyy-MM-dd HH:mm:ss');
  else return '';
}

export {formattedDateTime};