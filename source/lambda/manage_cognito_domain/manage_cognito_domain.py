#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import boto3
import cfnresponse
from aws_lambda_powertools import Logger

logger = Logger()


# This custom resource will delete the Domain from a Cognito UserPool
# on each stack delete or stack update.
# It will also create a new Domain for the given UserPool
# on each stack create or stack update.
# The custom resource only handles the domain, it does not create/delete the UserPool itself.
# The purpose of handling the Domain through a custom resource instead of a CDK resource
# is to support a change of the domain on stack update,
# as is required when customers update the solution from <v1.1.0 to v1.1.0
def lambda_handler(event, context):
    request_type = event.get('RequestType')
    resource_properties = event.get('ResourceProperties', {})
    old_resource_properties = event.get('OldResourceProperties', {})
    user_pool_id = resource_properties.get('UserPoolId')
    domain_prefix = resource_properties.get('DomainPrefix')
    old_domain_prefix = old_resource_properties.get('DomainPrefix') if request_type == 'Update' else None

    cognito_idp = boto3.client('cognito-idp')

    if request_type in ['Delete']:
        # Delete the user pool domain
        domain_to_delete = old_domain_prefix if old_domain_prefix and old_domain_prefix != domain_prefix else domain_prefix
        try:
            cognito_idp.delete_user_pool_domain(
                Domain=domain_to_delete,
                UserPoolId=user_pool_id
            )
            logger.info(f"Deleted domain {domain_to_delete} for user pool {user_pool_id}")
        except Exception as error:
            logger.exception(f"Failed to delete domain: {error}")
            # on stack deletion, if domain has already been deleted, proceed gracefully
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
            return

    if request_type in ['Update']:
        # Delete the user pool domain
        domain_to_delete = old_domain_prefix if old_domain_prefix and old_domain_prefix != domain_prefix else domain_prefix
        try:
            cognito_idp.delete_user_pool_domain(
                Domain=domain_to_delete,
                UserPoolId=user_pool_id
            )
            logger.info(f"Deleted domain {domain_to_delete} for user pool {user_pool_id}")
        except Exception as error:
            logger.exception(f"Failed to delete domain: {error}")
            cfnresponse.send(event, context, cfnresponse.FAILED, {"error": "An error occurred"})
            return

    if request_type in ['Create', 'Update']:
        # (Re-)Create the user pool domain
        try:
            cognito_idp.create_user_pool_domain(
                Domain=domain_prefix,
                UserPoolId=user_pool_id
            )
            logger.info(f"Created domain {domain_prefix} for user pool {user_pool_id}")
        except Exception as error:
            logger.exception(f"Failed to create domain: {error}")
            cfnresponse.send(event, context, cfnresponse.FAILED, {"error": "An error occurred"})
            return

    cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
