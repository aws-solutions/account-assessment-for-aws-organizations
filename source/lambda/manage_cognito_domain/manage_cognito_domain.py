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
def _delete_user_pool_domain(cognito_idp, domain, user_pool_id, event, context, fail_on_error=True):
    try:
        cognito_idp.delete_user_pool_domain(
            Domain=domain,
            UserPoolId=user_pool_id
        )
        logger.info(f"Deleted domain {domain} for user pool {user_pool_id}")
        return True
    except Exception as error:
        logger.exception(f"Failed to delete domain: {error}")
        if fail_on_error:
            cfnresponse.send(event, context, cfnresponse.FAILED, {"error": "An error occurred"})
        else:
            # on stack deletion, if domain has already been deleted, proceed gracefully
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        return False


def _create_user_pool_domain(cognito_idp, domain, user_pool_id, event, context):
    try:
        cognito_idp.create_user_pool_domain(
            Domain=domain,
            UserPoolId=user_pool_id
        )
        logger.info(f"Created domain {domain} for user pool {user_pool_id}")
        return True
    except Exception as error:
        logger.exception(f"Failed to create domain: {error}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {"error": "An error occurred"})
        return False


def _get_domain_to_delete(domain_prefix, old_domain_prefix):
    return old_domain_prefix if old_domain_prefix and old_domain_prefix != domain_prefix else domain_prefix


def lambda_handler(event, context):
    request_type = event.get('RequestType')
    resource_properties = event.get('ResourceProperties', {})
    old_resource_properties = event.get('OldResourceProperties', {})
    user_pool_id = resource_properties.get('UserPoolId')
    domain_prefix = resource_properties.get('DomainPrefix')
    old_domain_prefix = old_resource_properties.get('DomainPrefix') if request_type == 'Update' else None

    cognito_idp = boto3.client('cognito-idp')

    if request_type == 'Delete':
        domain_to_delete = _get_domain_to_delete(domain_prefix, old_domain_prefix)
        if not _delete_user_pool_domain(cognito_idp, domain_to_delete, user_pool_id, event, context, fail_on_error=False):
            return

    if request_type == 'Update':
        domain_to_delete = _get_domain_to_delete(domain_prefix, old_domain_prefix)
        if not _delete_user_pool_domain(cognito_idp, domain_to_delete, user_pool_id, event, context, fail_on_error=True):
            return

    if request_type in ['Create', 'Update']:
        if not _create_user_pool_domain(cognito_idp, domain_prefix, user_pool_id, event, context):
            return

    cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
