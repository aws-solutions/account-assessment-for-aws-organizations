# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import re


def sanitize(name, space_allowed=False, replace_with_character='_'):
    """Sanitizes input string.

    Replaces any character other than [a-zA-Z0-9._-] in a string
    with a specified character (default '_').

    Args:
        name: Input string
        space_allowed (optional):
            Is there a space in the input string. Default to false.
        replace_with_character (optional):
            Character to replace the target character with. Default to '_'.

    Returns:
        Sanitized string

    Raises:
    """
    if space_allowed:
        sanitized_name = re.sub(r'([^\sa-zA-Z0-9._-])',
                                replace_with_character,
                                name)
    else:
        sanitized_name = re.sub(r'([^a-zA-Z0-9._-])',
                                replace_with_character,
                                name)
    return sanitized_name


def trim_length_from_end(string, length):
    """ Trims the length of the given string to the given length

    :param string:
    :param length:
    :return: trimmed string to the length provided
    """
    if len(string) > length:
        return string[:length]
    else:
        return string


def trim_string_from_front(string: str, remove: str):
    """ Remove string provided in the search_string
    and returns remainder of the string.
    :param string:
    :param remove:
    :return: trimmed string
    """
    if string.startswith(remove):
        return string[len(remove):]
    else:
        raise ValueError('The beginning of the string does '
                         'not match the string to be trimmed.')


def extract_string(search_str):
    return str[len(search_str):]


def convert_list_values_to_string(_list):
    return list(map(str, _list))


def trim_string_split_to_list_get_last_item(_string: str, separator: str = ':') -> str:
    """
    splits the string with give separator and remove whitespaces
    """
    return [x.strip() for x in _string.split(separator)][-1]
