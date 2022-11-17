# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json

from aws_lambda_powertools import Logger

from utils.datetime_json_encoder_iso_format import DateTimeISOFormatEncoder

logger = Logger()


def replace_key_in_dict(source_dict: dict, old_key: str, new_key: str) -> dict:
    """Replace key in the map with new key.
    :param
        source_dict: dict
        {
            "old_key": "old_value",
            "Key1": "Value1"
        }
        old_key: str
        new_key: str

    :return
        source_dict: dict
        {
            "new_key": "old_value",
            "Key1": "Value1"
        }
    """
    if old_key in source_dict.keys():
        source_dict.update({new_key: source_dict.get(old_key)})
        source_dict.pop(old_key)
    return source_dict


def replace_datetime_to_str_in_dict(source_dict: dict) -> dict:
    """Replace datetime type values in the map str type
        :param
            source_dict: dict
            {
                "OldKey": "old_value",
                "Key1": "Value1"
            }
            old_key: str
            new_key: str

        :return
            source_dict: dict
            {
                "NewKey": "old_value",
                "Key1": "Value1"
            }
        """
    return json.loads(json.dumps(source_dict, cls=DateTimeISOFormatEncoder))
