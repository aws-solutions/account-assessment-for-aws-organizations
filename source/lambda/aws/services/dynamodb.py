#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# !/bin/python
from os import getenv
from typing import Dict, List

from aws_lambda_powertools import Logger
from boto3.dynamodb.conditions import Key, Attr, ConditionBase
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from mypy_boto3_dynamodb.type_defs import QueryOutputTableTypeDef, ScanOutputTableTypeDef, \
    UpdateItemInputTableUpdateItemTypeDef, GetItemOutputTableTypeDef

from aws.utils.boto3_session import Boto3Session
from policy_explorer.policy_explorer_model import DdbPagination
from utils.list_utils import split_list_by_batch_size

MAX_BATCH_SIZE = 25


class DynamoDB:
    """
    This class performs CRUD operations on the given DynamoDB table
    """

    def __init__(self, table_name: str):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        dynamodb_resource: DynamoDBServiceResource = Boto3Session('dynamodb', region=getenv('AWS_REGION')).get_resource()
        self.table: Table = dynamodb_resource.Table(table_name)
        self.next_token_returned_msg = "Next Token Returned: {}"
        self.logger.debug("Initialized client for DynamoDB table: " + self.table.table_name)

    def put_items(self, items: list):
        """
        Create items list into chunks of
        MAX_BATCH_SIZE and put them into dynamodb table
        :param items: list of put items
        :return:
        """
        self.logger.debug(f"Putting following items in DynamoDB in batches :"
                          f" {items}")

        list_of_chunks = split_list_by_batch_size(items, MAX_BATCH_SIZE)
        for chunk in list_of_chunks:
            self.logger.debug(f"Adding {len(chunk)} items to "
                              f"DynamoDB: {chunk}")
            self.put_batch_items(chunk)

    def put_batch_items(self, chunk: List):
        """
        Adds items in batch of 25 items.
        """
        self.logger.debug(f"Putting following items in DynamoDB:"
                          f" {chunk}")
        try:
            with self.table.batch_writer() as writer:
                for item in chunk:
                    writer.put_item(
                        Item=item
                    )
        except Exception:
            self.logger.error(f"AWS_Solution_Error: Error while putting the "
                              f"items in the DynamoDB: {chunk}")
            raise
        self.logger.debug(f"Successfully entered the following items in the "
                          f"dynamoDB: {chunk}")

    def find_items_by_partition_key(self, value: str) -> List[Dict]:
        """
        find all items from the DynamoDB that match the given partition key
        :param
            value for the partition key
        :returns
            list of items that match the partition key. may be empty.
        """
        try:
            self.logger.debug(f"Getting following items in DynamoDB:"
                              f" {value}")
            response: QueryOutputTableTypeDef = self.table.query(
                KeyConditionExpression=Key('PartitionKey').eq(value)
            )
            return response.get('Items')
        except Exception:
            self.logger.error(f"AWS_Solution_Error: Error while getting the "
                              f"items in the DynamoDB: {value}")
            raise

    def find_items_by_partition_key_paginated(self, value: str, pagination: DdbPagination = dict()) -> Dict:

        try:

            limit = pagination.get('Limit', 100)
            query_params = {
                'KeyConditionExpression': Key('PartitionKey').eq(value),
                'Limit': limit
            }
            
            if pagination.get('ExclusiveStartKey'):
                query_params['ExclusiveStartKey'] = pagination['ExclusiveStartKey']
            
            response: QueryOutputTableTypeDef = self.table.query(**query_params)
            
            return {
                'Items': response.get('Items', []),
                'LastEvaluatedKey': response.get('LastEvaluatedKey'),
                'Count': response.get('Count', 0),
                'ScannedCount': response.get('ScannedCount', 0)
            }
        except Exception:
            self.logger.error(f"AWS_Solution_Error: Error while getting paginated "
                              f"items from DynamoDB: {value}")
            raise

    def find_all(self) -> List[Dict]:
        self.logger.debug(f"Getting all items from DynamoDB table {self.table.table_name}:")
        response: ScanOutputTableTypeDef = self.table.scan()
        return response['Items']

    def get_by_id(self, partition_key, sort_key) -> Dict:
        self.logger.debug(f"Getting item from DynamoDB table {self.table.table_name}:")
        response: GetItemOutputTableTypeDef = self.table.get_item(
            Key={
                'PartitionKey': partition_key,
                'SortKey': sort_key
            }
        )
        return response['Item']

    def put_item(self, item):
        self.table.put_item(Item=item)
        self.logger.debug(f"Trying to add or replace item in table {self.table.table_name}: "
                          f"{item}")
        self.table.put_item(Item=item)
        self.logger.debug(f"Added or replaced item in table {self.table.table_name}: "
                          f"{item}")

    def update_item(self, kwargs: UpdateItemInputTableUpdateItemTypeDef):
        self.logger.debug(f"Trying  to update item in table {self.table.table_name}: "
                          f"{kwargs['Key']}")
        self.table.update_item(**kwargs)
        self.logger.debug(f"Updated item in table {self.table.table_name}: "
                          f"{kwargs['Key']}")

    def query(self, partition_key,
              sort_key_prefix='',
              filters: Dict = dict(),
              pagination: DdbPagination = dict()
              ) -> List[Dict]:
        self.logger.debug(
            f"Querying DynamoDB table {self.table.table_name} for Keys {partition_key}/{sort_key_prefix}")

        # Start with the KeyConditionExpression
        key_condition_expression = Key('PartitionKey').eq(partition_key) & Key('SortKey').begins_with(sort_key_prefix)

        # Initialize FilterExpression dynamically based on filters dict
        filter_expression = None
        for attr_name, attr_value in filters.items():
            self.logger.debug(
                f"Adding filter {attr_name} with value {attr_value}")
            if filter_expression is None:
                filter_expression = Attr(attr_name).contains(attr_value)
            else:
                filter_expression = filter_expression & Attr(attr_name).contains(attr_value)

        limit = pagination.get('Limit', 5000)  # Use old default for backward compatibility
        query_params: dict = dict(
            KeyConditionExpression=key_condition_expression,
            Limit=limit,
        )
        if pagination.get('ExclusiveStartKey'):
            query_params['ExclusiveStartKey'] = pagination['ExclusiveStartKey']
        if filter_expression is not None:
            query_params['FilterExpression'] = filter_expression

        # Execute the query with the filter expression if present
        response: QueryOutputTableTypeDef = self.table.query(**query_params)

        return response['Items']

    def query_paginated(self, partition_key,
                       sort_key_prefix='',
                       filters: Dict = dict(),
                       pagination: DdbPagination = dict()
                       ) -> Dict:
        key_condition_expression = Key('PartitionKey').eq(partition_key) & Key('SortKey').begins_with(sort_key_prefix)

        filter_expression = None
        for attr_name, attr_value in filters.items():
            self.logger.debug(f"Adding filter {attr_name} with value {attr_value}")
            if filter_expression is None:
                filter_expression = Attr(attr_name).contains(attr_value)
            else:
                filter_expression = filter_expression & Attr(attr_name).contains(attr_value)

        requested_limit = pagination.get('Limit', 100)
        start_key = pagination.get('ExclusiveStartKey')
        
        # When filters are present, iterate through pages to collect enough filtered results
        if filter_expression is not None:
            return self._query_with_filter_pagination(
                key_condition_expression,
                filter_expression,
                requested_limit,
                start_key
            )
        
        # No filters - simple query with limit
        query_params: dict = dict(
            KeyConditionExpression=key_condition_expression,
            Limit=requested_limit,
        )
        if start_key:
            query_params['ExclusiveStartKey'] = start_key

        response: QueryOutputTableTypeDef = self.table.query(**query_params)

        return {
            'Items': response['Items'],
            'LastEvaluatedKey': response.get('LastEvaluatedKey'),
            'Count': response.get('Count', 0),
            'ScannedCount': response.get('ScannedCount', 0)
        }

    def _query_with_filter_pagination(
        self,
        key_condition_expression: ConditionBase,
        filter_expression: ConditionBase,
        requested_limit: int,
        start_key: Dict = None
    ) -> Dict:
        collected_items: List[Dict] = []
        last_evaluated_key = start_key
        total_scanned = 0
        
        # Use larger batch size for internal pagination to reduce API calls
        batch_size = 1000
        
        while len(collected_items) < requested_limit:
            query_params: dict = dict(
                KeyConditionExpression=key_condition_expression,
                FilterExpression=filter_expression,
                Limit=batch_size,
            )
            if last_evaluated_key:
                query_params['ExclusiveStartKey'] = last_evaluated_key

            response: QueryOutputTableTypeDef = self.table.query(**query_params)
            
            collected_items.extend(response.get('Items', []))
            total_scanned += response.get('ScannedCount', 0)
            last_evaluated_key = response.get('LastEvaluatedKey')
            
            self.logger.debug(f"Filter pagination: collected {len(collected_items)} items, scanned {total_scanned}")
            
            # No more items to scan
            if not last_evaluated_key:
                break
        
        result_items = collected_items[:requested_limit]
        has_more_collected = len(collected_items) > requested_limit
        has_more_in_table = last_evaluated_key is not None
        
        next_page_key = None
        if has_more_collected or has_more_in_table:
            if has_more_collected and result_items:

                last_item = result_items[-1]
                next_page_key = {
                    'PartitionKey': last_item['PartitionKey'],
                    'SortKey': last_item['SortKey']
                }
            else:
                # We didn't trim, use DynamoDB's LastEvaluatedKey
                next_page_key = last_evaluated_key
        
        return {
            'Items': result_items,
            'LastEvaluatedKey': next_page_key,
            'Count': len(result_items),
            'ScannedCount': total_scanned
        }

    def delete_item(self, key):
        self.logger.debug(f"Trying to delete item from table {self.table.table_name}: {key}")
        self.table.delete_item(Key=key)
        self.logger.debug(f"Deleted item from table {self.table.table_name}: {key}")

    def find_items_by_secondary_index(self, index_name: str, key: str, index_value: str) -> List[Dict]:
        self.logger.debug(
            f"Trying to find item from table {self.table.table_name} by index {index_name} with key {key} and value {index_value}")
        response: ScanOutputTableTypeDef = self.table.query(
            IndexName=index_name,
            KeyConditionExpression=Key(key).eq(index_value),
        )
        data = response['Items']

        while 'LastEvaluatedKey' in response:
            response = self.table.query(
                IndexName=index_name,
                KeyConditionExpression=Key(key).eq(index_value),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            data.extend(response['Items'])
        self.logger.debug('Found {} items.'.format(len(data)))
        return data
