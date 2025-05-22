// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {CfnParameter, CfnResource, Stack, StackProps} from "aws-cdk-lib";
import {Construct} from "constructs";
import {ArnPrincipal, CompositePrincipal, PolicyDocument, PolicyStatement, Role} from "aws-cdk-lib/aws-iam";
import {addCfnSuppressRules} from '@aws-solutions-constructs/core';
import {DELEGATED_ADMIN_SCAN, POLICY_EXPLORER_SCAN, TRUSTED_ACCESS_SCAN} from "./account-assessment-hub-stack";
import {addCfnGuardSuppressions} from "./helpers/add-cfn-guard-suppression";


export const ORG_MANAGEMENT_ROLE_NAME = 'AccountAssessment-OrgMgmtStackRole';

interface OrgManagementAccountStackProps extends StackProps {

}

export class OrgManagementAccountStack extends Stack {
  public readonly hubAccountId: string;

  constructor(scope: Construct, id: string, props: OrgManagementAccountStackProps) {
    super(scope, id, props);

    const namespace = new CfnParameter(this, 'DeploymentNamespace', {
      description: 'Will be used as prefix for resource names. Same namespace must be used in hub stack.',
      type: 'String',
      minLength: 3,
      maxLength: 10,
      allowedPattern: '^[a-z0-9][a-z0-9-]{1,8}[a-z0-9]$',
      constraintDescription: 'Must be 3-10 characters long, containing only lowercase letters, numbers, and hyphens. Cannot begin or end with a hyphen.'
    });

    const hubAccountIdParameter = new CfnParameter(this, 'HubAccountId', {
      description: 'ID of the AWS account where the Hub Stack of this solution is deployed.',
      type: 'String'
    });
    this.hubAccountId = hubAccountIdParameter.valueAsString;


    this.templateOptions.metadata = {
      "AWS::CloudFormation::Interface": {
        ParameterGroups: [
          {
            Label: {default: "Solution Setup"},
            Parameters: [namespace.logicalId, hubAccountIdParameter.logicalId]
          }
        ],
        ParameterLabels: {
          [namespace.logicalId]: {
            default: "Provide the unique namespace value from Hub deployment",
          },
          [hubAccountIdParameter.logicalId]: {
            default: "Provide the Hub Account Id",
          }
        },
      },
    };


    const organizationPolicyStatement = new PolicyStatement({
      actions: [
        'organizations:ListAccounts',
        'organizations:ListAccountsForParent',
        'organizations:ListDelegatedAdministrators',
        'organizations:ListDelegatedServicesForAccount',
        'organizations:ListAWSServiceAccessForOrganization',
        'organizations:DescribePolicy',
        'organizations:ListPolicies'
      ],
      resources: ["*"],
    });

    const role = new Role(this, 'OrgManagementStackRole', {
      roleName: `${namespace.valueAsString}-${this.region}-${ORG_MANAGEMENT_ROLE_NAME}`,
      assumedBy: new CompositePrincipal(
        new ArnPrincipal(`arn:aws:iam::${this.hubAccountId}:role/${namespace.valueAsString}-${this.region}-${TRUSTED_ACCESS_SCAN}`),
        new ArnPrincipal(`arn:aws:iam::${this.hubAccountId}:role/${namespace.valueAsString}-${this.region}-${DELEGATED_ADMIN_SCAN}`),
        new ArnPrincipal(`arn:aws:iam::${this.hubAccountId}:role/${namespace.valueAsString}-${this.region}-${POLICY_EXPLORER_SCAN}`)
      ),
      inlinePolicies: {
        listAccounts: new PolicyDocument({
          statements: [organizationPolicyStatement]
        })
      }
    });
    addCfnGuardSuppressions(role.node.defaultChild as CfnResource, ["IAM_NO_INLINE_POLICY_CHECK"]);
    addCfnSuppressRules(role, [{
      id: 'W11',
      reason: 'Resource * is necessary for organizations:List* operations. No risk, because the role can still only access its own organization.'
    }, {
      id: 'W28',
      reason: 'This role needs an explicit name so that the Hub Stack can reference the role.'
    }]);
  }
}