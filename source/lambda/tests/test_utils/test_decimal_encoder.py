# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import decimal
import json

from utils.decimal_json_encoder import DecimalJsonEncoder


def test_decimal_encoder():
    assert json.dumps(
        {'x': decimal.Decimal('5.5')}, cls=DecimalJsonEncoder) == json.dumps(
        {'x': 5.5})
    assert json.dumps(
        {'x': decimal.Decimal('5.0')}, cls=DecimalJsonEncoder) == json.dumps(
        {'x': 5})
    encoder = DecimalJsonEncoder()
    assert encoder.encode({'x': decimal.Decimal('5.65')}) == json.dumps(
        {'x': 5.65})
    assert encoder.encode({'x': decimal.Decimal('5.0')}) == json.dumps(
        {'x': 5})
    assert encoder.encode(
        {'x': decimal.Decimal('5.0'),
         'y': decimal.Decimal('5.5')}) == json.dumps({'x': 5, 'y': 5.5})

