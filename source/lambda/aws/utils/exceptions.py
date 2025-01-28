# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from functools import wraps
from os import getenv

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError, EndpointConnectionError, ConnectTimeoutError
logger = Logger(service='service_exception_handler', level=getenv('LOG_LEVEL'))


def service_exception_handler(func):
    @wraps(func)
    def wrapper_func(self, *args, **kwargs):
        try:
            response = func(self, *args, **kwargs)
        except ClientError as err:
            if err.response['Error']['Code'] == 'UnrecognizedClientException' or \
                    err.response['Error']['Code'] == 'InvalidClientTokenId':
                raise RegionNotEnabled(self.region)
            elif err.response['Error']['Code'] == "503":
                raise ServiceUnavailable(self.region)
            elif err.response['Error']['Code'] == "AccessDeniedException":
                raise AccessDenied(self.region)
            else:
                logger.error(err)
                raise
        except EndpointConnectionError:
            raise ServiceUnavailable(self.region)
        except ConnectTimeoutError:
            raise ConnectionTimeout(self.region)
        return response
    return wrapper_func


def resource_not_found_exception_handler(func):
    @wraps(func)
    def wrapper_func(self, *args, **kwargs):
        try:
            response = func(self, *args, **kwargs)
        except ClientError as err:
            exception_codes = [
                'ResourceNotFoundException',
                'NoSuchEntityException',
                'RepositoryPolicyNotFoundException',
                'PolicyNotFound',
                'NotFoundException',
                'NoSuchBucketPolicy',
                'PolicyNotFoundException',
                'InvalidParameterException'
            ]
            if err.response['Error']['Code'] in exception_codes:
                logger.error(str(err))
                return {'Error': str(err)}
            else:
                logger.error(err)
                raise
        return response
    return wrapper_func


class RegionNotEnabled(Exception):
    def __init__(self, region):
        self.region = region
        self.message = f"{region} is disabled, you must enable it before scanning resources in this region."
        super().__init__(self.message)


class ServiceUnavailable(Exception):
    def __init__(self, region):
        self.region = region
        self.message = f"Service is not available in {region}."
        super().__init__(self.message)


class ConnectionTimeout(Exception):
    def __init__(self, region):
        self.region = region
        self.message = f"Service endpoint connection timed out in {region}"
        super().__init__(self.message)


class AccessDenied(Exception):
    def __init__(self, region):
        self.region = region
        self.message = f"Caught AccessDenied Exception in {region}"
        super().__init__(self.message)


class AccountAssessmentClientException(Exception):
    pass
