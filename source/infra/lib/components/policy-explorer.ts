// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {AttributeType, BillingMode, Table, TableEncryption,} from "aws-cdk-lib/aws-dynamodb";
import * as iam from "aws-cdk-lib/aws-iam";
import {CfnPolicy, CfnRole, PolicyStatement} from "aws-cdk-lib/aws-iam";
import {Construct} from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import {Runtime} from "aws-cdk-lib/aws-lambda";
import * as events from "aws-cdk-lib/aws-events";
import {EventbridgeToLambda, EventbridgeToLambdaProps} from "@aws-solutions-constructs/aws-eventbridge-lambda";
import {CfnParameter, Duration} from "aws-cdk-lib";
import {AuthorizationType, LambdaIntegration, RestApi,} from "aws-cdk-lib/aws-apigateway";
import {CognitoAuthenticationResources} from "./cognito-authenticator";
import {StateMachine} from "aws-cdk-lib/aws-stepfunctions";
import {addCfnSuppressRules} from "@aws-solutions-constructs/core";
import {createStateMachine} from "./policy-explorer-state-machine";

export const SPOKE_EXECUTION_ROLE_NAME = "AccountAssessment-Spoke-ExecutionRole";
export const VALIDATION_ACCOUNT_ACCESS_ROLE_NAME = 'ValidateSpokeAccess'
export const POLICY_SCAN_SPOKE_RESOURCES_ROLE_NAME = 'PolicyExplorerScanSpokeResource'
export const POLICY_SCAN_SINGLE_ACCOUNT_ROLE_NAME = 'PolicyExplorerScanSingleAccountResource'
export const ORG_MANAGEMENT_ROLE_NAME = 'AccountAssessment-OrgMgmtStackRole';

export interface PolicyExplorerScanComponentProps {
  api: RestApi;
  apiResourcePath: string;
  componentTableConfig: {
    partitionKeyName: string;
    sortKeyName: string;
  };
  assetCode: lambda.AssetCode;
  tables: {
    jobHistory: Table,
  },
  functions: {
    readJob: lambda.Function,
  }
  componentConfig: {
    readHandlerPath: string,
    apiResourcePath: string,
    tableEnvVariableName: string,
    powertoolsServiceName: string
    dynamoTtlInDays: CfnParameter,
    solutionVersion: string,
    stackId: string,
    sendAnonymousData: string
  }
  roleAssumedByApiGateway: iam.ServicePrincipal;
  dynamoDbRoleName: string;
  cognitoAuthenticationResources: CognitoAuthenticationResources;
  namespace: CfnParameter;
  region: string,
  partition: string,
  accountId: string,
}

export class PolicyExplorerScanComponent extends Construct {
  
  public readonly componentTable: Table;
  public readonly stateMachine: StateMachine;

  constructor(
    scope: Construct,
    id: string,
    props: PolicyExplorerScanComponentProps
  ) {
    super(scope, id);

    const componentSubDirectoryInLambdaCode = 'policy_explorer';
    
    this.componentTable = new Table(this, "Table", {
      partitionKey: {
        name: props.componentTableConfig.partitionKeyName,
        type: AttributeType.STRING,
      },
      sortKey: {
        name: props.componentTableConfig.sortKeyName,
        type: AttributeType.STRING,
      },
      encryption: TableEncryption.AWS_MANAGED,
      billingMode: BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: "ExpiresAt",
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
        recoveryPeriodInDays: 10
      },
    });

    const dynamoDbRole = new iam.Role(this, props.dynamoDbRoleName, {
      assumedBy: props.roleAssumedByApiGateway,
    });

    const dynamoDbPolicyStatement = new PolicyStatement();
    dynamoDbPolicyStatement.addActions("dynamodb:Query");
    dynamoDbPolicyStatement.addResources(this.componentTable.tableArn);

    dynamoDbRole.addToPolicy(dynamoDbPolicyStatement);

    // has to match AssessmentType. referenced via DynamoDB(os.getenv(assessment_type))
    props.functions.readJob.addEnvironment(props.componentConfig.tableEnvVariableName, this.componentTable.tableName);
    this.componentTable.grantReadWriteData(props.functions.readJob);
    this.componentTable.addGlobalSecondaryIndex({
      indexName: 'JobId',
      partitionKey: {name: 'JobId', type: AttributeType.STRING},
    });

    const validateAccountAccessFunction = new lambda.Function(this, 'ValidateSpokeAccess', {
      runtime: lambda.Runtime.PYTHON_3_12,
      tracing: lambda.Tracing.ACTIVE,
      timeout: Duration.minutes(15),
      memorySize: 1024,
      code: props.assetCode,
      handler: `${componentSubDirectoryInLambdaCode}/step_functions_lambda/validate_account_access.lambda_handler`,
      environment: {
        COMPONENT_TABLE: this.componentTable.tableName,
        TABLE_JOBS: props.tables.jobHistory.tableName,
        TIME_TO_LIVE_IN_DAYS: props.componentConfig.dynamoTtlInDays.valueAsString,
        SPOKE_ROLE_NAME: `${props.namespace.valueAsString}-${props.region}-${SPOKE_EXECUTION_ROLE_NAME}`,
        NAMESPACE: props.namespace.valueAsString,
        LOG_LEVEL: 'INFO',
        POWERTOOLS_SERVICE_NAME: 'Scan' + props.componentConfig.powertoolsServiceName,
        SOLUTION_VERSION: props.componentConfig.solutionVersion,
        STACK_ID: props.componentConfig.stackId,
        SEND_ANONYMOUS_DATA: props.componentConfig.sendAnonymousData
      }
    });
  
    props.tables.jobHistory.grantReadWriteData(validateAccountAccessFunction);

    const scanFunction = new lambda.Function(this, 'StartScan', {
      runtime: lambda.Runtime.PYTHON_3_12,
      tracing: lambda.Tracing.ACTIVE,
      timeout: Duration.minutes(2),
      code: props.assetCode,
      handler: 'policy_explorer/start_state_machine_execution_to_scan_services.lambda_handler',
      environment: {
        COMPONENT_TABLE: this.componentTable.tableName,
        TABLE_JOBS: props.tables.jobHistory.tableName,
        TIME_TO_LIVE_IN_DAYS: props.componentConfig.dynamoTtlInDays.valueAsString,
        NAMESPACE: props.namespace.valueAsString,
        ORG_MANAGEMENT_ROLE_NAME: `${props.namespace.valueAsString}-${props.region}-${ORG_MANAGEMENT_ROLE_NAME}`,
        LOG_LEVEL: 'INFO',
        POWERTOOLS_SERVICE_NAME: 'Scan' + props.componentConfig.powertoolsServiceName,
        SOLUTION_VERSION: props.componentConfig.solutionVersion,
        STACK_ID: props.componentConfig.stackId,
        SEND_ANONYMOUS_DATA: props.componentConfig.sendAnonymousData
      }
    });

    const policyExplorerScanSpokeResourceFunction = new lambda.Function(this, 'PolicyExplorerScanSpokeResource', {
      runtime: lambda.Runtime.PYTHON_3_12,
      tracing: lambda.Tracing.ACTIVE,
      timeout: Duration.minutes(15),
      memorySize: 512,
      code: props.assetCode,
      handler: `${componentSubDirectoryInLambdaCode}/step_functions_lambda/scan_policy_all_services_router.lambda_handler`,
      environment: {
        COMPONENT_TABLE: this.componentTable.tableName,
        TABLE_JOBS: props.tables.jobHistory.tableName,
        TIME_TO_LIVE_IN_DAYS: props.componentConfig.dynamoTtlInDays.valueAsString,
        POLICY_ITEM_TTL_IN_DAYS: '1',
        SPOKE_ROLE_NAME: `${props.namespace.valueAsString}-${props.region}-${SPOKE_EXECUTION_ROLE_NAME}`,
        NAMESPACE: props.namespace.valueAsString,
        ORG_MANAGEMENT_ROLE_NAME: `${props.namespace.valueAsString}-${props.region}-${ORG_MANAGEMENT_ROLE_NAME}`,
        LOG_LEVEL: 'INFO',
        POWERTOOLS_SERVICE_NAME: 'ScanResourceBasedPolicyInSpokeAccount',
        SOLUTION_VERSION: props.componentConfig.solutionVersion,
        STACK_ID: props.componentConfig.stackId,
        SEND_ANONYMOUS_DATA: props.componentConfig.sendAnonymousData
      }
    });

    const policyExplorerScanSpokeResourceRoleCfnRef = policyExplorerScanSpokeResourceFunction.role?.node.defaultChild as CfnRole
    policyExplorerScanSpokeResourceRoleCfnRef.roleName = `${props.namespace.valueAsString}-${props.region}-${POLICY_SCAN_SPOKE_RESOURCES_ROLE_NAME}`

    policyExplorerScanSpokeResourceFunction.addToRolePolicy(new PolicyStatement({
      actions: ['sts:AssumeRole'],
      resources: ["arn:aws:iam::*:role/" + `${props.namespace.valueAsString}-${props.region}-${SPOKE_EXECUTION_ROLE_NAME}`],
    }));
    this.componentTable.grantReadWriteData(policyExplorerScanSpokeResourceFunction);
    props.tables.jobHistory.grantReadWriteData(policyExplorerScanSpokeResourceFunction);

    const policyExplorerScanSingleAccountFunction = new lambda.Function(this, 'PolicyExplorerScanSingleAccount', {
      runtime: lambda.Runtime.PYTHON_3_12,
      tracing: lambda.Tracing.ACTIVE,
      timeout: Duration.seconds(29), // max timeout through API Gateway
      memorySize: 3584,
      code: props.assetCode,
      handler: `${componentSubDirectoryInLambdaCode}/scan_single_service.lambda_handler`,
      environment: {
        COMPONENT_TABLE: this.componentTable.tableName,
        TABLE_JOBS: props.tables.jobHistory.tableName,
        TIME_TO_LIVE_IN_DAYS: props.componentConfig.dynamoTtlInDays.valueAsString,
        POLICY_ITEM_TTL_IN_DAYS: '1',
        NAMESPACE: props.namespace.valueAsString,
        SPOKE_ROLE_NAME: `${props.namespace.valueAsString}-${props.region}-${SPOKE_EXECUTION_ROLE_NAME}`,
        ORG_MANAGEMENT_ROLE_NAME: `${props.namespace.valueAsString}-${props.region}-${ORG_MANAGEMENT_ROLE_NAME}`,
        LOG_LEVEL: 'INFO',
        POWERTOOLS_SERVICE_NAME: 'ScanResourceBasedPolicyInSpokeAccount',
        SOLUTION_VERSION: props.componentConfig.solutionVersion,
        STACK_ID: props.componentConfig.stackId,
        SEND_ANONYMOUS_DATA: props.componentConfig.sendAnonymousData
      }
    });

    const policyExplorerScanSingleAccountRoleCfnRef = policyExplorerScanSingleAccountFunction.role?.node.defaultChild as CfnRole
    policyExplorerScanSingleAccountRoleCfnRef.roleName = `${props.namespace.valueAsString}-${props.region}-${POLICY_SCAN_SINGLE_ACCOUNT_ROLE_NAME}`

    policyExplorerScanSingleAccountFunction.addToRolePolicy(new PolicyStatement({
      actions: ['sts:AssumeRole'],
      resources: ["arn:aws:iam::*:role/" + `${props.namespace.valueAsString}-${props.region}-${SPOKE_EXECUTION_ROLE_NAME}`],
    }));
    this.componentTable.grantReadWriteData(policyExplorerScanSingleAccountFunction);
    props.tables.jobHistory.grantReadWriteData(policyExplorerScanSingleAccountFunction);

    const finishScan = new lambda.Function(this, 'FinishAsyncJob', {
      runtime: lambda.Runtime.PYTHON_3_12,
      tracing: lambda.Tracing.ACTIVE,
      timeout: Duration.minutes(1),
      code: props.assetCode,
      handler: `${componentSubDirectoryInLambdaCode}/finish_scan.lambda_handler`,
      environment: {
        COMPONENT_TABLE: this.componentTable.tableName,
        TABLE_JOBS: props.tables.jobHistory.tableName,
        TIME_TO_LIVE_IN_DAYS: props.componentConfig.dynamoTtlInDays.valueAsString,
        POWERTOOLS_SERVICE_NAME: 'FinishScanForResourceBasedPolicies',
        SOLUTION_VERSION: props.componentConfig.solutionVersion,
        STACK_ID: props.componentConfig.stackId,
        SEND_ANONYMOUS_DATA: props.componentConfig.sendAnonymousData
      }
    });
    props.tables.jobHistory.grantReadWriteData(finishScan);
    this.componentTable.grantReadWriteData(finishScan);

    const stateMachineName = `${props.namespace.valueAsString}-PolicyExplorerScan-StateMachine`
    this.stateMachine = createStateMachine(this, stateMachineName, validateAccountAccessFunction, policyExplorerScanSpokeResourceFunction, finishScan);

    //This statement is required for the Default Policy generated by Step function CDK to get the policy to start execution on itself, if this is not set the DISTRIBUTED execution mode will not work.
    const stateMachineDefaultPolicy = this.stateMachine.role.node.findChild("DefaultPolicy").node.findChild("Resource") as CfnPolicy
    stateMachineDefaultPolicy.addOverride("Properties.PolicyDocument.Statement.4", 
      {
        "Action": "states:StartExecution",
              "Effect": "Allow",
              "Resource": [
                `arn:${props.partition}:states:${props.region}:${props.accountId}:stateMachine:${stateMachineName}`
              ]
      })

    scanFunction.addEnvironment('SCAN_POLICIES_STATE_MACHINE_ARN', this.stateMachine.stateMachineArn);
    scanFunction.addToRolePolicy(new PolicyStatement({
      actions: ['states:StartExecution'],
      resources: [this.stateMachine.stateMachineArn],
    }));

    const startScanFunctionRole_cfn_ref = scanFunction.role?.node.defaultChild as CfnRole
    startScanFunctionRole_cfn_ref.roleName = `${props.namespace.valueAsString}-${props.region}-${props.componentConfig.powertoolsServiceName}`

    const validateAccountAccessRole_cfn_ref = validateAccountAccessFunction.role?.node.defaultChild as CfnRole
    validateAccountAccessRole_cfn_ref.roleName = `${props.namespace.valueAsString}-${props.region}-${VALIDATION_ACCOUNT_ACCESS_ROLE_NAME}`

    validateAccountAccessFunction.addToRolePolicy(new PolicyStatement({
      actions: ['sts:AssumeRole'],
      resources: [`arn:aws:iam::*:role/${props.namespace.valueAsString}-${props.region}-${SPOKE_EXECUTION_ROLE_NAME}`],
    }))

    scanFunction.addToRolePolicy(new PolicyStatement({
      actions: ['organizations:DescribeOrganization'],
      resources: ["*"],
    }));
    scanFunction.addToRolePolicy(new PolicyStatement({
      actions: ['sts:AssumeRole'],
      resources: [`arn:aws:iam::*:role/${props.namespace.valueAsString}-${props.region}-${ORG_MANAGEMENT_ROLE_NAME}`],
    })); 

    policyExplorerScanSpokeResourceFunction.addToRolePolicy(new PolicyStatement({
      actions: ['sts:AssumeRole'],
      resources: [`arn:aws:iam::*:role/${props.namespace.valueAsString}-${props.region}-${ORG_MANAGEMENT_ROLE_NAME}`],
    })); 


    const scanFunctionDefaultPolicy = scanFunction.node.tryFindChild('ServiceRole')
      ?.node.findChild('DefaultPolicy')
      .node.findChild('Resource') as CfnPolicy;
    scanFunctionDefaultPolicy && addCfnSuppressRules(scanFunctionDefaultPolicy, [{
      id: 'W12',
      reason: 'Resource * is necessary for organizations:List* operations. No risk, because the role can still only access its own organization.'
    }]);


    this.componentTable.grantReadWriteData(scanFunction);
    props.tables.jobHistory.grantReadWriteData(scanFunction);

    const eventbridgeToLambdaProps: EventbridgeToLambdaProps = {
      existingLambdaObj: scanFunction,
      eventRuleProps: {
        enabled: true,
        schedule: events.Schedule.cron({minute: "00", hour: "23",})
      }
    };

    new EventbridgeToLambda(this, 'policy-explorer-schedule-rule', eventbridgeToLambdaProps);


    const policyExplorerApiResource = props.api.root.addResource(`${props.apiResourcePath}`);
    const readResourcePolicy = policyExplorerApiResource.addResource(`{partitionKey}`)

    const readFunction = new lambda.Function(this, 'Read', {
      runtime: Runtime.PYTHON_3_12,
      tracing: lambda.Tracing.ACTIVE,
      timeout: Duration.minutes(1),
      code: props.assetCode,
      handler: props.componentConfig.readHandlerPath,
      environment: {
        COMPONENT_TABLE: this.componentTable.tableName,
        TABLE_JOBS: props.tables.jobHistory.tableName,
        NAMESPACE: props.namespace.valueAsString,
        POWERTOOLS_SERVICE_NAME: 'Read' + props.componentConfig.powertoolsServiceName,
        SOLUTION_VERSION: props.componentConfig.solutionVersion,
        STACK_ID: props.componentConfig.stackId,
        SEND_ANONYMOUS_DATA: props.componentConfig.sendAnonymousData
      }
    });
    this.componentTable.grantReadData(readFunction);

    readResourcePolicy.addMethod('GET', new LambdaIntegration(readFunction), {
      authorizationType: AuthorizationType.COGNITO,
      authorizer: {
        authorizerId: props.cognitoAuthenticationResources.authorizerFullAccess.ref
      },
      authorizationScopes: ['account-assessment-api/api']
    });

    policyExplorerApiResource.addResource('scan').addMethod('POST', new LambdaIntegration(policyExplorerScanSingleAccountFunction), {
      authorizationType: AuthorizationType.COGNITO,
      authorizer: {
        authorizerId: props.cognitoAuthenticationResources.authorizerFullAccess.ref
      },
      authorizationScopes: ['account-assessment-api/api']
    });
  }
}
