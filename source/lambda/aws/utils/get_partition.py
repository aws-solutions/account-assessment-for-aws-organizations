# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from os import getenv


def partition_name_for_current_region():
    region_name = getenv('AWS_REGION')
    china_region_name_prefix = 'cn'
    us_gov_cloud_region_name_prefix = 'us-gov'
    aws_regions_partition = 'aws'
    aws_china_regions_partition = 'aws-cn'
    aws_us_gov_cloud_regions_partition = 'aws-us-gov'

    # China regions
    if region_name.startswith(china_region_name_prefix):
        return aws_china_regions_partition
    # AWS GovCloud(US) Regions
    elif region_name.startswith(us_gov_cloud_region_name_prefix):
        return aws_us_gov_cloud_regions_partition
    else:
        return aws_regions_partition
