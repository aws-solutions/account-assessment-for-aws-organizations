# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import policy_explorer.policy_explorer_model as model


def get_policy_details_from_arn(resource_arn: str) -> dict:
    """Splits ARN and populates a subset of the PolicyDetails object. Some Services don't have region information and they should
    populated based on scan job running. example ssm-incidents
    arn:aws:ssm-incidents::111111111111:incident-record/dfdf/34c57e00-19d3-ee2e-6a0d-9344a03cadc5

    Args:
        resource_arn (str):
        Uses the pattern 
        # arn:partition:service:region:account-id:resource-id
        # arn:partition:service:region:account-id:resource-type/resource-id
        # arn:partition:service:region:account-id:resource-type:resource-id
        # https://docs.aws.amazon.com/IAM/latest/UserGuide/reference-arns.html

    Raises:
        ValueError: Invalid Arn if parameter resource_arn is None or 
        the number of components in arn is less than 6 after splitting on `:`

    Returns:
        PolicyDetails: PolicyDetails only the following parameters are populated from the arn
        AccountId
        Service
        ResourceIdentifier
        Region
    """
    if resource_arn is not None:
        arn_components = resource_arn.split(":")
        
        if len(arn_components) == 6:
            policy_details: model.PolicyDetails = {
                "AccountId": arn_components[4],
                "Service": arn_components[2],
                "ResourceIdentifier": arn_components[5],
                "Region": arn_components[3]
            }
            return policy_details
        elif len(arn_components) >= 7:
            policy_details: model.PolicyDetails = {
                "AccountId": arn_components[4],
                "Service": arn_components[2],
                "ResourceIdentifier": f"{arn_components[5]}:{arn_components[6]}",
                "Region": arn_components[3]
            }
            return policy_details
        else:
            raise ValueError("Invalid ARN " + resource_arn)
    else:
        raise ValueError("Missing ARN")