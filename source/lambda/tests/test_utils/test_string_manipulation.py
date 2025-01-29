#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from utils import string_manipulation


def test_sanitize():
    non_sanitized_string = 'I s@nitize $tring exc*pt_underscore-hypen.'
    sanitized_string_allow_space = 'I s_nitize _tring exc_pt_underscore-hypen.'
    sanitized_string_no_space_replace_hypen = \
        'I-s-nitize--tring-exc-pt_underscore-hypen.'
    assert string_manipulation.sanitize(non_sanitized_string,True) == \
           sanitized_string_allow_space
    assert string_manipulation.sanitize(non_sanitized_string, False,'-') == \
           sanitized_string_no_space_replace_hypen


def test_trim_length():
    actual_sting = "EighteenCharacters"
    eight_char_string = "Eighteen"
    assert string_manipulation\
               .trim_length_from_end(actual_sting, 8) == eight_char_string
    assert string_manipulation\
               .trim_length_from_end(actual_sting, 18) == actual_sting
    assert string_manipulation\
               .trim_length_from_end(actual_sting, 20) == actual_sting


def test_extract_string():
    actual_string = "abcdefgh"
    extract_string = "defgh"
    assert string_manipulation.trim_string_from_front(actual_string, 'abc') == \
           extract_string


def test_convert_list_values_to_string():
    list_of_numbers = [11, 22, 33, 44]
    list_of_strings = string_manipulation.convert_list_values_to_string(list_of_numbers)
    for string in list_of_strings:
        assert isinstance(string, str)


def test_convert_string_to_list_default_separator():
    separator = ','
    value = "a, b, c"
    last_value = string_manipulation.trim_string_split_to_list_get_last_item(value, separator)
    assert isinstance(last_value, str)
    assert last_value == 'c'


def test_convert_string_to_list_no_separator():
    separator = ','
    value = "a"
    last_value = string_manipulation.trim_string_split_to_list_get_last_item(value, separator)
    assert isinstance(last_value, str)
    assert last_value == 'a'


def test_convert_string_to_list_custom_separator():
    separator = ':'
    value = "a:b"
    last_value = string_manipulation.trim_string_split_to_list_get_last_item(value, separator)
    assert isinstance(last_value, str)
    assert last_value == 'b'


def test_convert_stack_id_to_uuid():
    separator = '/'
    value = "arn:aws:cloudformation:us-east-1:111111111:stack/account-assessment-for-aws-organizations-hub/7c5d2820-55a8-11ed-a7a3-1202153a549b"
    last_value = string_manipulation.trim_string_split_to_list_get_last_item(value, separator)
    assert isinstance(last_value, str)
    assert last_value == '7c5d2820-55a8-11ed-a7a3-1202153a549b'


def test_convert_string_to_list_then_trim_string_from_front():
    value = "arn:aws:service:region-ID:account-ID:report/report-ID"
    last_value = string_manipulation.trim_string_from_front(
        string_manipulation.trim_string_split_to_list_get_last_item(value),
        remove='report/'
    )
    assert isinstance(last_value, str)
    assert last_value == 'report-ID'
