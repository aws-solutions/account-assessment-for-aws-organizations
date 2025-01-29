#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import datetime

from aws_lambda_powertools import Logger
from dateutil.tz import tzlocal

from utils.dict_manipulation import replace_key_in_dict, \
    replace_datetime_to_str_in_dict

logger = Logger()


def test_replace_dict_key():
    old_key = "OldKey"
    new_key = "NewKey"
    existing_key = "Key1"
    mapping = {
        old_key: "old_value",
        existing_key: "Value1"
    }
    new_mapping = replace_key_in_dict(mapping, old_key, new_key)
    logger.info(new_mapping)
    assert new_key in new_mapping.keys()
    assert old_key not in new_mapping.keys()
    assert existing_key in new_mapping.keys()


def test_replace_datetime_to_str_in_dict():
    old_mapping = {
        'Arn': 'arn:aws:organizations::999999999999:account/o-6d3y5hgnah/823024189466',
        'Email': 'dev@mock',
        'Name': 'Developer1',
        'Status': 'ACTIVE',
        'JoinedMethod': 'CREATED',
        'JoinedTimestamp': datetime.datetime(2022, 7, 15, 15, 56, 57, 735683,
                                             tzinfo=tzlocal()),
        'DelegationEnabledDate': datetime.datetime(2022, 7, 15, 15, 56, 57,
                                                   750048, tzinfo=tzlocal()),
        'AccountId': '823024187886965735629466'}

    new_mapping = replace_datetime_to_str_in_dict(old_mapping)
    assert type(old_mapping.get('JoinedTimestamp')) == datetime.datetime
    assert type(old_mapping.get('DelegationEnabledDate')) == datetime.datetime
    assert type(new_mapping.get('JoinedTimestamp')) == str
    assert type(new_mapping.get('DelegationEnabledDate')) == str



