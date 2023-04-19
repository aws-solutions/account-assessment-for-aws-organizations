// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  Aspects,
  Aws,
  CfnCondition,
  CfnMapping,
  CfnParameter,
  CfnResource,
  Fn,
  IAspect,
  Resource,
  Stack,
  Tags,
} from "aws-cdk-lib";
import * as appreg from "@aws-cdk/aws-servicecatalogappregistry-alpha";
import { CfnApplication } from "aws-cdk-lib/aws-applicationinsights";
import { CfnAttributeGroupAssociation, CfnResourceAssociation, } from "aws-cdk-lib/aws-servicecatalogappregistry";
import { CfnResourceShare } from "aws-cdk-lib/aws-ram";
import { IConstruct } from "constructs";

export interface AppRegisterProps {
  solutionId: string;
  solutionName: string;
  solutionDomain: string;
  solutionVersion: string;
  appRegistryApplicationName: string;
  applicationType: string;
}

export class AppRegister {
  private readonly solutionId: string;
  private readonly solutionName: string;
  private readonly solutionVersion: string;
  private readonly appRegistryApplicationName: string;
  private readonly applicationType: string;

  constructor(props: AppRegisterProps) {
    this.solutionId = props.solutionId;
    this.appRegistryApplicationName = props.appRegistryApplicationName;
    this.solutionName = props.solutionName;
    this.applicationType = props.applicationType;
    this.solutionVersion = props.solutionVersion;
  }

  public applyAppRegistryToStacks(
    hubStack: Stack,
    spokeStacks: Stack[],
    nestedStacks: Stack[]
  ) {
    const application = this.createAppRegistry(hubStack);
    if (spokeStacks.length > 0) {
      this.allowHubStackToShareApplication(application, hubStack);
      spokeStacks.forEach((spokeStack) =>
        this.applyAppRegistryToSpokeStack(spokeStack)
      );
    }
    nestedStacks.forEach((nestedStack) => {
      application.associateApplicationWithStack(nestedStack);
    });
  }

  private createAppRegistry(stack: Stack): appreg.Application {
    const map = this.createMap(stack);

    const application = new appreg.Application(stack, "AppRegistry", {
      applicationName: Fn.join("-", [
        map.findInMap("Data", "AppRegistryApplicationName"),
        Aws.REGION,
        Aws.ACCOUNT_ID,
      ]),
      description: `Service Catalog application to track and manage all your resources for the solution ${this.solutionName}`,
    });
    application.associateApplicationWithStack(stack);

    const attributeGroup = new appreg.AttributeGroup(
      stack,
      "DefaultApplicationAttributeGroup",
      {
        attributeGroupName: Fn.join("-", [
          "A3O",
          Aws.REGION,
          Aws.STACK_NAME
        ]),
        description: "Attribute group for solution information",
        attributes: {
          applicationType: map.findInMap("Data", "ApplicationType"),
          version: map.findInMap("Data", "Version"),
          solutionID: map.findInMap("Data", "ID"),
          solutionName: map.findInMap("Data", "SolutionName"),
        },
      }
    );

    application.associateAttributeGroup(attributeGroup);

    const appInsights = new CfnApplication(
      stack,
      "ApplicationInsightsConfiguration",
      {
        resourceGroupName: Fn.join("-", [
          "AWS_AppRegistry_Application",
          map.findInMap("Data", "AppRegistryApplicationName"),
          Aws.REGION,
          Aws.ACCOUNT_ID,
        ]),
        autoConfigurationEnabled: true,
        cweMonitorEnabled: true,
        opsCenterEnabled: true,
      }
    );

    applyDependsOn(appInsights, application);

    this.applyTagsToApplication(application, map);

    return application;
  }

  private createMap(stack: Stack) {
    const map = new CfnMapping(stack, "Solution");
    map.setValue("Data", "ID", this.solutionId);
    map.setValue("Data", "Version", this.solutionVersion);
    map.setValue(
      "Data",
      "AppRegistryApplicationName",
      this.appRegistryApplicationName
    );
    map.setValue("Data", "SolutionName", this.solutionName);
    map.setValue("Data", "ApplicationType", this.applicationType);

    return map;
  }

  private allowHubStackToShareApplication(
    application: appreg.Application,
    hubStack: Stack
  ) {
    const orgId = new CfnParameter(hubStack, "OrganizationID", {
      description:
        "Organization ID to support multi account deployment. Leave blank for single account deployments.",
      type: "String",
      allowedPattern: "^$|^o-[a-z0-9]{10,32}$",
      default: "",
    });

    const managementAccountId = new CfnParameter(
      hubStack,
      "ManagementAccountId",
      {
        description:
          "Account ID for the management account of the Organization. Leave blank for single account deployments.",
        type: "String",
        default: "",
      }
    );

    const appRegisterHubCfnInterface = {
      ParameterGroups: [
        {
          Label: {default: "Application Manager Configuration"},
          Parameters: [orgId.logicalId, managementAccountId.logicalId]
        }
      ],
      ParameterLabels: {
        [orgId.logicalId]: {
          default: "Provide the AWS Organization ID",
        },
        [managementAccountId.logicalId]: {
          default: "Provide the Org Management Account ID",
        }
      },
    };
    this.mergeOrSetCfnInterface(hubStack, appRegisterHubCfnInterface);


    const multiAccountDeployment = new CfnCondition(
      hubStack,
      "MultiAccountDeployment",
      {
        expression: Fn.conditionOr(
          Fn.conditionNot(Fn.conditionEquals(orgId.valueAsString, "")),
          Fn.conditionNot(
            Fn.conditionEquals(managementAccountId.valueAsString, "")
          )
        ),
      }
    );

    const resourceShare = new CfnResourceShare(hubStack, "ApplicationShare", {
      name: Aws.STACK_NAME,
      allowExternalPrincipals: false,
      permissionArns: [
        "arn:aws:ram::aws:permission/AWSRAMPermissionServiceCatalogAppRegistryApplicationAllowAssociation",
      ],
      principals: [
        `arn:${Aws.PARTITION}:organizations::${managementAccountId.valueAsString}:organization/${orgId.valueAsString}`,
      ],
      resourceArns: [application.applicationArn],
    });
    Aspects.of(resourceShare).add(new ConditionAspect(multiAccountDeployment));
  }

  private mergeOrSetCfnInterface(stack: Stack, cfnInterface: {
    ParameterGroups: { Parameters: string[]; Label: { default: string } }[];
    ParameterLabels: { [p: string]: { default: string } }
  }) {
    if (stack.templateOptions.metadata) {
      stack.templateOptions.metadata["AWS::CloudFormation::Interface"].ParameterGroups = [
        ...(stack.templateOptions.metadata["AWS::CloudFormation::Interface"].ParameterGroups),
        ...cfnInterface.ParameterGroups
      ];
      stack.templateOptions.metadata["AWS::CloudFormation::Interface"].ParameterLabels = {
        ...(stack.templateOptions.metadata["AWS::CloudFormation::Interface"].ParameterLabels),
        ...cfnInterface.ParameterLabels
      };

    } else {
      stack.templateOptions.metadata = {
        "AWS::CloudFormation::Interface": cfnInterface,
      };
    }
  }

  private applyAppRegistryToSpokeStack(spokeStack: Stack) {

    const hubAccountId = (spokeStack as any).hubAccountId || new CfnParameter(spokeStack, "HubAccountId", {
      description: 'ID of the AWS account where the Hub Stack of this solution is deployed.',
      type: 'String'
    }).valueAsString;

    const applicationManagerEnabled = new CfnParameter(spokeStack, 'ApplicationManagerEnabled', {
      description: 'Select "Yes" if you provided Application Manager Configuration details in hub stack.',
      allowedValues: ['Yes', 'No'],
      default: 'Yes'
    });

    const appRegisterSpokeCfnInterface = {
      ParameterGroups: [
        {
          Label: {default: "Application Manager Configuration"},
          Parameters: [applicationManagerEnabled.logicalId]
        }
      ],
      ParameterLabels: {
        [applicationManagerEnabled.logicalId]: {
          default: "Create Resource Association",
        }
      }
    };
    this.mergeOrSetCfnInterface(spokeStack, appRegisterSpokeCfnInterface);

    const appManagerCondition = new CfnCondition(spokeStack, 'AppRegistryEnabledCondition', {
      expression: Fn.conditionEquals(applicationManagerEnabled.valueAsString, 'Yes')
    });

    const map = this.createMap(spokeStack);

    const resourceAssociation = new CfnResourceAssociation(spokeStack, "AppRegistryStackAssociation", {
      application: Fn.join("-", [
        map.findInMap("Data", "AppRegistryApplicationName"),
        Aws.REGION,
        hubAccountId,
      ]),
      resource: Aws.STACK_ID,
      resourceType: "CFN_STACK",
    });

    resourceAssociation.addOverride('Condition', appManagerCondition.logicalId);

    const attributeGroup = new appreg.AttributeGroup(
      spokeStack,
      "DefaultApplicationAttributeGroup",
      {
        attributeGroupName: Fn.join("-", [
          "A3O",
          Aws.REGION,
          Aws.STACK_NAME
        ]),
        description: "Attribute group for solution information",
        attributes: {
          applicationType: map.findInMap("Data", "ApplicationType"),
          version: map.findInMap("Data", "Version"),
          solutionID: map.findInMap("Data", "ID"),
          solutionName: map.findInMap("Data", "SolutionName"),
        },
      }
    );

    const attributeGroupAssociation = new CfnAttributeGroupAssociation(
      spokeStack,
      "AppRegistryApplicationAttributeAssociation",
      {
        application: Fn.join("-", [
          map.findInMap("Data", "AppRegistryApplicationName"),
          Aws.REGION,
          hubAccountId,
        ]),
        attributeGroup: attributeGroup.attributeGroupId,
      }
    );

    attributeGroupAssociation.addOverride('Condition', appManagerCondition.logicalId);

  }
  
  private applyTagsToApplication(
    application: appreg.Application,
    map: CfnMapping
  ) {
    applyTag(application, "Solutions:SolutionID", map.findInMap("Data", "ID"));
    applyTag(
      application,
      "Solutions:SolutionName",
      map.findInMap("Data", "SolutionName")
    );
    applyTag(application, "Solutions:SolutionVersion", map.findInMap("Data", "Version"));
    applyTag(
      application,
      "Solutions:ApplicationType",
      map.findInMap("Data", "ApplicationType")
    );
  }
}

export class ConditionAspect implements IAspect {

  readonly condition: CfnCondition;

  constructor(condition: CfnCondition) {
    this.condition = condition;
  }

  public visit(node: IConstruct) {
    if (node instanceof CfnResource) {
      applyCondition(node, this.condition);
    }
  }
}

function applyCondition(
  resource: Resource | CfnResource,
  condition: CfnCondition
) {
  if (resource) {
    if (resource instanceof Resource)
      resource = resource.node.defaultChild as CfnResource;
    resource.cfnOptions.condition = condition;
  }
}

export function applyTag(resource: IConstruct, key: string, value: string) {
  Tags.of(resource).add(key, value);
}

export function applyDependsOn(
  dependee: Resource | CfnResource,
  parent: Resource
) {
  if (dependee) {
    if (dependee instanceof Resource)
      dependee = dependee.node.defaultChild as CfnResource;
    dependee.addDependency(parent.node.defaultChild as CfnResource);
  }
}