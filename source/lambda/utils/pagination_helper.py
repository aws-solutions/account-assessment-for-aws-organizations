#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
import base64
from typing import Dict, Any
from aws_lambda_powertools import Logger
from utils.pagination_model import PaginationParams, PaginationMetadata, DdbPagination

logger = Logger()

def validate_max_results(max_results_param) -> int:
    if not max_results_param:
        return 100
    
    try:
        max_results = int(max_results_param)
        if max_results > 1000:
            return 1000
        elif max_results < 1:
            return 100
        return max_results
    except (ValueError, TypeError):
        return 100

def decode_next_token(next_token: str | None) -> Dict[str, Any] | None:
    if not next_token:
        return None
    
    try:
        decoded_token = base64.b64decode(next_token).decode('utf-8')
        return json.loads(decoded_token)
    except (json.JSONDecodeError, ValueError, Exception) as e:
        logger.warning(f"Invalid nextToken provided: {e}")
        return None

def encode_next_token(last_evaluated_key: Dict[str, Any]) -> str | None:
    if not last_evaluated_key:
        return None
        
    try:
        token_json = json.dumps(last_evaluated_key)
        return base64.b64encode(token_json.encode('utf-8')).decode('utf-8')
    except Exception as e:
        logger.warning(f"Failed to encode nextToken: {e}")
        return None

def extract_pagination_params(query_params: Dict[str, str]) -> PaginationParams:
    max_results_param = query_params.get('maxResults') or query_params.get('limit')
    max_results = validate_max_results(max_results_param)
    exclusive_start_key = decode_next_token(query_params.get('nextToken'))
    
    return {
        'maxResults': max_results,
        'nextToken': exclusive_start_key
    }

def build_ddb_pagination(pagination_params: PaginationParams) -> DdbPagination:
    return {
        'Limit': pagination_params['maxResults'] or 100,
        'ExclusiveStartKey': pagination_params['nextToken']
    }

def build_pagination_metadata(last_evaluated_key: Dict[str, Any]) -> PaginationMetadata:
    has_more = last_evaluated_key is not None and bool(last_evaluated_key)
    next_token = encode_next_token(last_evaluated_key) if has_more else None
    
    return {
        'nextToken': next_token,
        'hasMoreResults': has_more
    }
