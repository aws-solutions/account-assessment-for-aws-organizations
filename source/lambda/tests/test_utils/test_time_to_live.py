#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from os import environ


def test_that_it_converts_1_day_to_seconds():
    # ARRANGE
    environ['TIME_TO_LIVE_IN_DAYS'] = '1'
    from utils.base_repository import get_seconds_to_live

    # ACT
    milliseconds = get_seconds_to_live()

    # ASSERT
    assert milliseconds == 86400


def test_that_it_returns_90_days_by_default():
    # ARRANGE
    environ['TIME_TO_LIVE_IN_DAYS'] = ''
    from utils.base_repository import get_seconds_to_live

    # ACT
    milliseconds = get_seconds_to_live()

    # ASSERT
    assert milliseconds == 7776000
