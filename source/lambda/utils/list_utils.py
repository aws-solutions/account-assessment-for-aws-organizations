# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools import Logger
logger = Logger('info')


def compare_lists(existing_list: list, new_list: list) -> bool:
    """Compares two list and return boolean flag if they match

    :param:
        existing_list: Input string
            Is there a space in the input string. Default to false.
        new_list:
            Character to replace the target character with. Default to '_'.

    :return:
        boolean value
    """
    added_values = list(set(new_list) - set(existing_list))
    removed_values = list(set(existing_list) - set(new_list))
    if len(added_values) == 0 and len(removed_values) == 0:
        logger.info("Lists matched.")
        return True
    else:
        logger.info("Lists didn't match.")
        return False


def convert_string_to_sorted_list_with_no_whitespaces(_string, delimiter=',') -> list:
    return sorted(_string.replace(' ', '').split(delimiter))


def remove_none_values_from_the_list(list_with_none_value: list) -> list:
    return list(filter(lambda item: item is not None, list_with_none_value))
