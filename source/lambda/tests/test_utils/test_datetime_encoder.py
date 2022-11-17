# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
from datetime import datetime

from utils.datetime_json_encoder_iso_format import DateTimeISOFormatEncoder

# ARRANGE
DATE_TIME = "2020-02-17T23:38:26"
datetime_str = '02/17/20 23:38:26'
datetime_object = datetime.strptime(datetime_str, '%m/%d/%y %H:%M:%S')
date_object = datetime_object.date()
encoder = DateTimeISOFormatEncoder()


def describe_encode():
    def test_it_encodes_datetime_in_dict():
        # ACT
        encoded_result = encoder.encode({"datetime": datetime_object})

        # ASSERT
        assert encoded_result == json.dumps({"datetime": DATE_TIME})

    def test_it_encodes_date_in_dict():
        # ACT
        encoded_result = encoder.encode({"date": date_object})

        # ASSERT
        assert encoded_result == json.dumps(
            {"date": "2020-02-17"})

    def test_it_encodes_both_date_and_datetime_in_dict():
        # ACT
        encoded_result = encoder.encode({"date": date_object, "datetime": datetime_object})

        # ASSERT
        assert encoded_result == json.dumps(
            {"date": "2020-02-17", "datetime": DATE_TIME})


def describe_when_passed_to_json_dumps():
    def test_it_encodes_datetime():
        # ACT
        encoded_result = json.dumps({"datetime": datetime_object}, cls=DateTimeISOFormatEncoder)

        # ASSERT
        assert encoded_result == json.dumps(
            {"datetime": DATE_TIME})

    def test_it_encodes_date_object():
        # ACT
        encoded_result = json.dumps({"date": date_object}, cls=DateTimeISOFormatEncoder)

        # ASSERT
        assert encoded_result == json.dumps(
            {"date": "2020-02-17"})
