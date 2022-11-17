# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# !/bin/python
from os import getenv
from typing import Dict, List

import boto3
from aws_lambda_powertools import Logger
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from mypy_boto3_dynamodb.type_defs import QueryOutputTableTypeDef, ScanOutputTableTypeDef, \
    UpdateItemInputTableUpdateItemTypeDef, GetItemOutputTableTypeDef

MAX_BATCH_SIZE = 25


class DynamoDB:
    """
    This class performs CRUD operations on the given DynamoDB table
    """

    def __init__(self, table_name: str):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        dynamodb_resource: DynamoDBServiceResource = boto3.resource('dynamodb')
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

        list_of_chunks = self.split_list_by_batch_size(items)
        for chunk in list_of_chunks:
            self.logger.debug(f"Adding {len(chunk)} items to "
                              f"DynamoDB: {chunk}")
            self.put_batch_items(chunk)

    def split_list_by_batch_size(self, large_list: list,
                                 batch_size=MAX_BATCH_SIZE) -> List[List]:
        self.logger.debug(f"Creating the list of batches for the list"
                          f" {large_list} with batch size as {MAX_BATCH_SIZE}")
        chunk_start_indexes = range(0, len(large_list), batch_size)
        chunks = [large_list[chunk_start:chunk_start + batch_size]
                  for chunk_start in chunk_start_indexes]
        self.logger.debug(f"Returning following batches: {chunks}")
        return chunks

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

    def query(self, partition_key, sort_key_prefix='') -> List[Dict]:
        self.logger.debug(
            f"Querying DynamoDB table {self.table.table_name} for Keys {partition_key}/{sort_key_prefix}:")
        response: QueryOutputTableTypeDef = self.table.query(
            KeyConditionExpression=Key('PartitionKey').eq(partition_key) & Key('SortKey').begins_with(sort_key_prefix)
        )
        return response['Items']

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
            response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        return data
