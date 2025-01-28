# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from os import getenv
from aws_lambda_powertools import Logger

from mypy_boto3_account import AccountClient
from mypy_boto3_account.type_defs import  ListRegionsResponseTypeDef, RegionTypeDef
from aws.utils.boto3_session import Boto3Session

class AccountService:
    
    def __init__(self, **kwargs):
        self.logger = Logger(service=self.__class__.__name__, level=getenv('LOG_LEVEL'))
        boto_session = Boto3Session('account', **kwargs)
        self.account_client: AccountClient = boto_session.get_client()
        
    def get_regions(self, account_id: str) -> list[str]:
        
        region_opt_in_statuses = ["ENABLED", "ENABLED_BY_DEFAULT"]
        response: ListRegionsResponseTypeDef = self.account_client.list_regions(
            RegionOptStatusContains=region_opt_in_statuses
        )
        regions: list[RegionTypeDef] = response.get("Regions", [])
        next_token = response.get("NextToken", None)
        
        while next_token is not None:
             response = self.account_client.list_regions(
                 RegionOptStatusContains=region_opt_in_statuses,
                 NextToken=next_token
             )
             regions.extend(response.get("Regions", []))
             next_token = response.get("NextToken", None)
       
        regions_to_scan = list(region.get('RegionName') for region in regions)
       
        self.logger.debug(f"Regions enabled or enabled by default for account_id {account_id} are {regions_to_scan}")
        return regions_to_scan