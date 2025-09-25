#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
import base64
from utils.pagination_helper import (
    validate_max_results,
    decode_next_token,
    encode_next_token,
    extract_pagination_params,
    build_ddb_pagination,
    build_pagination_metadata
)


def describe_pagination_helper():

    def test_validate_max_results_with_valid_string():
        # ARRANGE & ACT
        result = validate_max_results('50')
        
        # ASSERT
        assert result == 50

    def test_validate_max_results_with_valid_integer():
        # ARRANGE & ACT
        result = validate_max_results(50)
        
        # ASSERT
        assert result == 50

    def test_validate_max_results_with_max_cap():
        # ARRANGE & ACT
        result = validate_max_results('2000')
        
        # ASSERT
        assert result == 1000  # Should be capped at 1000

    def test_validate_max_results_with_zero():
        # ARRANGE & ACT
        result = validate_max_results('0')
        
        # ASSERT
        assert result == 100  # Should default to 100

    def test_validate_max_results_with_negative():
        # ARRANGE & ACT
        result = validate_max_results('-5')
        
        # ASSERT
        assert result == 100  # Should default to 100

    def test_validate_max_results_with_invalid_string():
        # ARRANGE & ACT
        result = validate_max_results('invalid')
        
        # ASSERT
        assert result == 100  # Should default to 100

    def test_validate_max_results_with_none():
        # ARRANGE & ACT
        result = validate_max_results(None)
        
        # ASSERT
        assert result == 100  # Should default to 100

    def test_validate_max_results_with_empty_string():
        # ARRANGE & ACT
        result = validate_max_results('')
        
        # ASSERT
        assert result == 100  # Should default to 100

    def test_encode_next_token_with_valid_key():
        # ARRANGE
        last_evaluated_key = {
            'PartitionKey': 'test-partition',
            'SortKey': 'test-sort'
        }
        
        # ACT
        result = encode_next_token(last_evaluated_key)
        
        # ASSERT
        assert result is not None
        assert isinstance(result, str)
        
        # Verify it can be decoded back
        decoded = base64.b64decode(result).decode('utf-8')
        parsed = json.loads(decoded)
        assert parsed == last_evaluated_key

    def test_encode_next_token_with_none():
        # ARRANGE & ACT
        result = encode_next_token(None)
        
        # ASSERT
        assert result is None

    def test_encode_next_token_with_empty_dict():
        # ARRANGE & ACT
        result = encode_next_token({})
        
        # ASSERT
        assert result is None

    def test_decode_next_token_with_valid_token():
        # ARRANGE
        original_data = {
            'PartitionKey': 'test-partition',
            'SortKey': 'test-sort'
        }
        token_json = json.dumps(original_data)
        next_token = base64.b64encode(token_json.encode('utf-8')).decode('utf-8')
        
        # ACT
        result = decode_next_token(next_token)
        
        # ASSERT
        assert result == original_data

    def test_decode_next_token_with_invalid_token():
        # ARRANGE & ACT
        result = decode_next_token('invalid-token')
        
        # ASSERT
        assert result is None

    def test_decode_next_token_with_none():
        # ARRANGE & ACT
        result = decode_next_token(None)
        
        # ASSERT
        assert result is None

    def test_decode_next_token_with_empty_string():
        # ARRANGE & ACT
        result = decode_next_token('')
        
        # ASSERT
        assert result is None

    def test_extract_pagination_params_with_max_results():
        # ARRANGE
        query_params = {
            'maxResults': '50'
        }
        
        # ACT
        result = extract_pagination_params(query_params)
        
        # ASSERT
        assert result['maxResults'] == 50
        assert result['nextToken'] is None

    def test_extract_pagination_params_with_limit():
        # ARRANGE
        query_params = {
            'limit': '25'
        }
        
        # ACT
        result = extract_pagination_params(query_params)
        
        # ASSERT
        assert result['maxResults'] == 25
        assert result['nextToken'] is None

    def test_extract_pagination_params_priority_max_results_over_limit():
        # ARRANGE
        query_params = {
            'limit': '25',
            'maxResults': '50'
        }
        
        # ACT
        result = extract_pagination_params(query_params)
        
        # ASSERT
        assert result['maxResults'] == 50  # Should prioritize maxResults

    def test_extract_pagination_params_with_next_token():
        # ARRANGE
        original_data = {'PartitionKey': 'test', 'SortKey': 'test'}
        token_json = json.dumps(original_data)
        next_token = base64.b64encode(token_json.encode('utf-8')).decode('utf-8')
        
        query_params = {
            'maxResults': '50',
            'nextToken': next_token
        }
        
        # ACT
        result = extract_pagination_params(query_params)
        
        # ASSERT
        assert result['maxResults'] == 50
        assert result['nextToken'] == original_data

    def test_extract_pagination_params_with_no_params():
        # ARRANGE
        query_params = {}
        
        # ACT
        result = extract_pagination_params(query_params)
        
        # ASSERT
        assert result['maxResults'] == 100  # Default
        assert result['nextToken'] is None

    def test_build_ddb_pagination():
        # ARRANGE
        pagination_params = {
            'maxResults': 50,
            'nextToken': {'PartitionKey': 'test', 'SortKey': 'test'}
        }
        
        # ACT
        result = build_ddb_pagination(pagination_params)
        
        # ASSERT
        assert result['Limit'] == 50
        assert result['ExclusiveStartKey'] == {'PartitionKey': 'test', 'SortKey': 'test'}

    def test_build_ddb_pagination_with_none_values():
        # ARRANGE
        pagination_params = {
            'maxResults': None,
            'nextToken': None
        }
        
        # ACT
        result = build_ddb_pagination(pagination_params)
        
        # ASSERT
        assert result['Limit'] == 100  # Default
        assert result['ExclusiveStartKey'] is None

    def test_build_pagination_metadata_with_more_results():
        # ARRANGE
        last_evaluated_key = {
            'PartitionKey': 'test-partition',
            'SortKey': 'test-sort'
        }
        
        # ACT
        result = build_pagination_metadata(last_evaluated_key)
        
        # ASSERT
        assert result['hasMoreResults'] is True
        assert result['nextToken'] is not None
        assert isinstance(result['nextToken'], str)

    def test_build_pagination_metadata_with_no_more_results():
        # ARRANGE & ACT
        result = build_pagination_metadata(None)
        
        # ASSERT
        assert result['hasMoreResults'] is False
        assert result['nextToken'] is None

    def test_build_pagination_metadata_with_empty_dict():
        # ARRANGE & ACT
        result = build_pagination_metadata({})
        
        # ASSERT
        assert result['hasMoreResults'] is False
        assert result['nextToken'] is None

    def test_round_trip_token_encoding_decoding():
        # ARRANGE
        original_data = {
            'PartitionKey': 'ResourceBasedPolicy',
            'SortKey': 'GLOBAL#some-unique-id',
            'NumericAttribute': 12345
        }
        
        # ACT - Encode then decode
        encoded_token = encode_next_token(original_data)
        decoded_data = decode_next_token(encoded_token)
        
        # ASSERT
        assert decoded_data == original_data

    def test_parameter_validation_boundary_conditions():
        # Test boundary conditions
        test_cases = [
            (1, 1),           # Minimum valid value
            (1000, 1000),     # Maximum valid value
            (1001, 1000),     # Just over max (should cap)
            (0, 100),         # Zero (should default)
            (-1, 100),        # Negative (should default)
            ('1', 1),         # String representation
            ('1000', 1000),   # String max
            ('1001', 1000),   # String over max
            (None, 100),      # None (should default)
            ('', 100),        # Empty string (should default)
            ('abc', 100),     # Invalid string (should default)
            (1.5, 1),         # Float (should convert to int)
            ('1.5', 100),     # String float (can't convert directly, should default)
        ]
        
        for input_val, expected in test_cases:
            result = validate_max_results(input_val)
            assert result == expected, f"Input {input_val} should return {expected}, got {result}"
