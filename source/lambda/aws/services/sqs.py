# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# !/bin/python

from os import getenv


from aws_lambda_powertools import Logger
from mypy_boto3_sqs.type_defs import GetQueueAttributesResultTypeDef, ListQueuesResultTypeDef
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session


class SQS:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('sqs', credentials=account_credentials, region=region)
        self.sqs_client = boto_session.get_client()

    @service_exception_handler
    def list_queues(self) -> list[str]:
        response: ListQueuesResultTypeDef = self.sqs_client.list_queues()

        queue_urls = response.get('QueueUrls', [])
        next_token = response.get('NextToken', None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.sqs_client.list_queues(
                NextToken=next_token
            )
            self.logger.info("Extending Queue URLs List")
            queue_urls.extend(response.get('QueueUrls', []))
            next_token = response.get('NextToken', None)

        return queue_urls

    @resource_not_found_exception_handler
    def get_queue_attributes(self, queue_url: str, attribute_names: list[str]) -> GetQueueAttributesResultTypeDef:
        response: GetQueueAttributesResultTypeDef = self.sqs_client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=attribute_names
        )
        self.logger.debug(f"Queue Attributes: {response}")
        return response


