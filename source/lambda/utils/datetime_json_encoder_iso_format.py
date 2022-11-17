# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# !/bin/python
import json
from datetime import datetime, date


class DateTimeISOFormatEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime, date)):
            serial = o.isoformat()
            return serial
        raise TypeError("Type %s not serializable" % type(o))
