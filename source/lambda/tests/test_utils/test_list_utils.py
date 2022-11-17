# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger

from utils.list_utils import compare_lists, convert_string_to_sorted_list_with_no_whitespaces, remove_none_values_from_the_list

logger = Logger('info')

list1 = ['aa', 'bb', 'cc']  # add value to list 2
list2 = ['aa', 'bb']  # remove value from list 1
list3 = ['aa', 'cc', 'dd']  # remove and add values from list 1
list4 = ['ee']  # single item list to test replace single account
list5 = ['ff']


def test_add_list():
    assert compare_lists(list2, list1) is False


def test_delete_list():
    assert compare_lists(list1, list2) is False


def test_add_delete_list():
    assert compare_lists(list1, list3) is False


def test_single_item_replacement():
    assert compare_lists(list4, list5) is False


def test_no_change_list():
    assert compare_lists(list1, list1) is True


def test_convert_string_to_sorted_list_with_no_whitespaces():
    # ARRANGE
    string1 = 'xxxxx'
    string2 = 'yyyyy'
    string3 = 'zzzzz'
    string = f'{string2}, {string3}, {string1}  '

    # ACT
    converted_list = convert_string_to_sorted_list_with_no_whitespaces(string)

    # ASSERT
    assert string1 in converted_list
    assert string2 in converted_list
    assert string3 in converted_list
    assert string not in converted_list
    # test sorted and no whitespace
    assert [string1, string2, string3] == converted_list


def test_remove_none_values_from_the_list():
    # ARRANGE
    list_with_none_value = ['a', None, 'b', None, 'c']

    # ACT
    no_none_value_list = remove_none_values_from_the_list(list_with_none_value)

    # ASSERT
    assert no_none_value_list == ['a', 'b', 'c']
