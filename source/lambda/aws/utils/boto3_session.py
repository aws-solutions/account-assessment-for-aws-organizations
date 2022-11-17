# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from os import getenv

from botocore.config import Config

# !/bin/python
import boto3


class Boto3Session:
    """This class initialize boto3 client for a given AWS service name.

    Example:
        class EC2(Boto3Session):
            def __init__(self, logger, region, **kwargs):
                __service_name = 'ec2'
                kwargs.update({'region': region}) # optional
                super().__init__(__service_name, **kwargs)
                self.ec2_client = super().get_client()
    """

    def __init__(self, service_name, **kwargs):
        """
            Parameters
            ----------
            region : str
                AWS region name. Example: 'us-east-1'
            service_name : str
                AWS service name. Example: 'ec2'
            credentials = dict, optional
                set of temporary AWS security credentials
            endpoint_url : str
                The complete URL to use for the constructed client.
        """
        self.service_name = service_name
        self.credentials = kwargs.get('credentials', None)
        self.region = kwargs.get('region', None)
        self.endpoint_url = kwargs.get('endpoint_url', None)
        self.solution_id = getenv('SOLUTION_ID', 'SO0217')
        self.solution_version = getenv('SOLUTION_VERSION', 'undefined')
        user_agent = f'AwsSolution/{self.solution_id}/{self.solution_version}'
        self.boto_config = Config(
            user_agent_extra=user_agent,
            retries={
                'mode': 'standard',
                'max_attempts': 5
            }
        )

    def get_client(self):
        """Creates a boto3 low-level service client by name.

        Returns: service client, type: Object
        """
        if self.credentials is None:
            if self.endpoint_url is None:
                return boto3.client(
                    self.service_name,
                    region_name=self.region,
                    config=self.boto_config
                )
            else:
                return boto3.client(
                    self.service_name, region_name=self.region,
                    config=self.boto_config,
                    endpoint_url=self.endpoint_url
                )
        else:
            if self.region is None:
                return boto3.client(
                    self.service_name,
                    aws_access_key_id=self.credentials.get('AccessKeyId'),
                    aws_secret_access_key=self.credentials.get('SecretAccessKey'),
                    aws_session_token=self.credentials.get('SessionToken'),
                    config=self.boto_config
                )
            else:
                return boto3.client(
                    self.service_name,
                    region_name=self.region,
                    aws_access_key_id=self.credentials.get('AccessKeyId'),
                    aws_secret_access_key=self.credentials.get('SecretAccessKey'),
                    aws_session_token=self.credentials.get('SessionToken'),
                    config=self.boto_config
                )

    def get_resource(self):
        """Creates a boto3 resource service client object by name

        Returns: resource service client, type: Object
        """
        if self.credentials is None:
            if self.endpoint_url is None:
                return boto3.resource(
                    self.service_name,
                    region_name=self.region,
                    config=self.boto_config
                )
            else:
                return boto3.resource(
                    self.service_name,
                    region_name=self.region,
                    config=self.boto_config,
                    endpoint_url=self.endpoint_url
                )
        else:
            if self.region is None:
                return boto3.resource(
                    self.service_name,
                    aws_access_key_id=self.credentials.get('AccessKeyId'),
                    aws_secret_access_key=self.credentials.get('SecretAccessKey'),
                    aws_session_token=self.credentials.get('SessionToken'),
                    config=self.boto_config
                )
            else:
                return boto3.resource(
                    self.service_name,
                    region_name=self.region,
                    aws_access_key_id=self.credentials.get('AccessKeyId'),
                    aws_secret_access_key=self.credentials.get('SecretAccessKey'),
                    aws_session_token=self.credentials.get('SessionToken'),
                    config=self.boto_config
                )
