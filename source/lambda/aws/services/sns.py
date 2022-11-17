# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from os import getenv

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError, EndpointConnectionError, ConnectTimeoutError
from mypy_boto3_sns.type_defs import GetTopicAttributesResponseTypeDef
from mypy_boto3_sns.type_defs import TopicTypeDef, ListTopicsResponseTypeDef

from aws.services.security_token_service import SecurityTokenService
from aws.utils.boto3_session import Boto3Session
from aws.utils.exceptions import service_exception_handler, resource_not_found_exception_handler


class SNS:
    def __init__(self, account_id, region):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        self.region = region
        role_name = getenv('SPOKE_ROLE_NAME')
        self.logger.debug(f"Assuming role {role_name} in {account_id} to scan service: {self.__class__.__name__}")
        account_credentials = SecurityTokenService().assume_role_by_name(account_id, role_name)
        boto_session = Boto3Session('sns', credentials=account_credentials, region=region)
        self.sns_client = boto_session.get_client()
        self.topic_arns = []

    @service_exception_handler
    def list_topics(self) -> list[TopicTypeDef]:
        response: ListTopicsResponseTypeDef = self.sns_client.list_topics()

        self.topic_arns = response.get('Topics', [])
        next_token = response.get('NextToken', None)

        while next_token is not None:
            self.logger.debug(f"Next Token Returned: {next_token})")
            response = self.sns_client.list_topics(
                NextToken=next_token
            )
            self.logger.info("Extending Topic ARNs List")
            self.topic_arns.extend(response.get('Topics', []))
            next_token = response.get('NextToken', None)

        return self.topic_arns

    @resource_not_found_exception_handler
    def get_topic_attributes(self, topic_arn: str) -> GetTopicAttributesResponseTypeDef:
        response: GetTopicAttributesResponseTypeDef = self.sns_client.get_topic_attributes(
            TopicArn=topic_arn
        )
        self.logger.debug(f"Topic Attributes: {response}")
        return response

