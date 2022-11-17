import {Construct} from "constructs";
import {AssessmentComponentProps, SimpleAssessmentComponent} from "./simple-assessment-component";
import * as lambda from "aws-cdk-lib/aws-lambda";
import {Runtime} from "aws-cdk-lib/aws-lambda";
import {CfnRole, PolicyStatement} from "aws-cdk-lib/aws-iam";
import {AuthorizationType, JsonSchemaType, LambdaIntegration} from "aws-cdk-lib/aws-apigateway";
import {createStateMachine} from "./resource-based-policy-state-machine";
import {Duration} from "aws-cdk-lib";

export const SPOKE_EXECUTION_ROLE_NAME = "AccountAssessment-Spoke-ExecutionRole";
export const VALIDATION_ACCOUNT_ACCESS_ROLE_NAME = 'ValidateSpokeAccountAccess'
export const SCAN_SPOKE_RESOURCES_ROLE_NAME = 'ScanSpokeResource'

export class ResourceBasedPolicyComponent extends SimpleAssessmentComponent {
  constructor(scope: Construct, id: string, props: AssessmentComponentProps) {
    // Creates API endpoint, Lambda functions "Read" and "Scan"
    super(scope, id, {
      ...props, requestValidation: {
        scanRequestBodyModelProps: {
          restApi: props.api,
          contentType: "application/json",
          description: "Validate the request body of ScanConfigurations",
          modelName: "ScanConfiguration",
          schema: {
            type: JsonSchemaType.OBJECT,
            properties: {
              AccountIds: {
                type: JsonSchemaType.ARRAY
              },
              OrgUnitIds: {
                type: JsonSchemaType.ARRAY
              },
              Regions: {
                type: JsonSchemaType.ARRAY
              },
              ServiceNames: {
                type: JsonSchemaType.ARRAY
              },
              ConfigurationName: {
                type: JsonSchemaType.STRING
              }
            },
          }
        }
      }
    });

    const {
      assetCode,
      api,
      cognitoAuthenticationResources,
      componentConfig,
      namespace,
      region,
      tables
    } = props;

    const componentSubDirectoryInLambdaCode = 'resource_based_policy';


    const validateAccountAccessFunction = new lambda.Function(this, 'ValidateSpokeAccountAccess', {
      runtime: lambda.Runtime.PYTHON_3_9,
      tracing: lambda.Tracing.ACTIVE,
      timeout: Duration.minutes(5),
      code: assetCode,
      handler: `${componentSubDirectoryInLambdaCode}/step_functions_lambda/validate_account_access.lambda_handler`,
      environment: {
        COMPONENT_TABLE: this.componentTable.tableName,
        TABLE_JOBS: tables.jobHistory.tableName,
        TIME_TO_LIVE_IN_DAYS: componentConfig.dynamoTtlInDays.valueAsString,
        SPOKE_ROLE_NAME: `${namespace.valueAsString}-${region}-${SPOKE_EXECUTION_ROLE_NAME}`,
        LOG_LEVEL: 'INFO',
        POWERTOOLS_SERVICE_NAME: 'Scan' + componentConfig.powertoolsServiceName,
        SOLUTION_VERSION: componentConfig.solutionVersion,
        STACK_ID: componentConfig.stackId,
        SEND_ANONYMOUS_DATA: componentConfig.sendAnonymousData
      }
    });

    const validateAccountAccessRoleCfnRef = validateAccountAccessFunction.role?.node.defaultChild as CfnRole
    validateAccountAccessRoleCfnRef.roleName = `${namespace.valueAsString}-${region}-${VALIDATION_ACCOUNT_ACCESS_ROLE_NAME}`

    validateAccountAccessFunction.addToRolePolicy(new PolicyStatement({
      actions: ['sts:AssumeRole'],
      resources: ["arn:aws:iam::*:role/" + `${namespace.valueAsString}-${region}-${SPOKE_EXECUTION_ROLE_NAME}`],
    }));

    tables.jobHistory.grantReadWriteData(validateAccountAccessFunction);

    const scanSpokeResourceFunction = new lambda.Function(this, 'ScanSpokeResource', {
      runtime: lambda.Runtime.PYTHON_3_9,
      tracing: lambda.Tracing.ACTIVE,
      timeout: Duration.minutes(15),
      code: assetCode,
      handler: `${componentSubDirectoryInLambdaCode}/step_functions_lambda/scan_policy_all_services_router.lambda_handler`,
      environment: {
        COMPONENT_TABLE: this.componentTable.tableName,
        TABLE_JOBS: tables.jobHistory.tableName,
        TIME_TO_LIVE_IN_DAYS: componentConfig.dynamoTtlInDays.valueAsString,
        SPOKE_ROLE_NAME: `${namespace.valueAsString}-${region}-${SPOKE_EXECUTION_ROLE_NAME}`,
        LOG_LEVEL: 'INFO',
        POWERTOOLS_SERVICE_NAME: 'ScanResourceBasedPolicyInSpokeAccount',
        SOLUTION_VERSION: componentConfig.solutionVersion,
        STACK_ID: componentConfig.stackId,
        SEND_ANONYMOUS_DATA: componentConfig.sendAnonymousData
      }
    });

    const scanSpokeResourceRoleCfnRef = scanSpokeResourceFunction.role?.node.defaultChild as CfnRole
    scanSpokeResourceRoleCfnRef.roleName = `${namespace.valueAsString}-${region}-${SCAN_SPOKE_RESOURCES_ROLE_NAME}`

    scanSpokeResourceFunction.addToRolePolicy(new PolicyStatement({
      actions: ['sts:AssumeRole'],
      resources: ["arn:aws:iam::*:role/" + `${namespace.valueAsString}-${region}-${SPOKE_EXECUTION_ROLE_NAME}`],
    }));
    this.componentTable.grantReadWriteData(scanSpokeResourceFunction);
    tables.jobHistory.grantReadWriteData(scanSpokeResourceFunction);

    const finishScan = new lambda.Function(this, 'FinishAsyncJob', {
      runtime: Runtime.PYTHON_3_9,
      tracing: lambda.Tracing.ACTIVE,
      timeout: Duration.seconds(20),
      code: assetCode,
      handler: `${componentSubDirectoryInLambdaCode}/finish_scan.lambda_handler`,
      environment: {
        COMPONENT_TABLE: this.componentTable.tableName,
        TABLE_JOBS: tables.jobHistory.tableName,
        TIME_TO_LIVE_IN_DAYS: componentConfig.dynamoTtlInDays.valueAsString,
        POWERTOOLS_SERVICE_NAME: 'FinishScanForResourceBasedPolicies',
        SOLUTION_VERSION: componentConfig.solutionVersion,
        STACK_ID: componentConfig.stackId,
        SEND_ANONYMOUS_DATA: componentConfig.sendAnonymousData
      }
    });
    tables.jobHistory.grantReadWriteData(finishScan);
    this.componentTable.grantReadWriteData(finishScan);


    const stateMachine = createStateMachine(this, validateAccountAccessFunction, scanSpokeResourceFunction, finishScan);

    this.functions.scanFunction.addEnvironment('SCAN_RESOURCE_POLICY_STATE_MACHINE_ARN', stateMachine.stateMachineArn);
    this.functions.scanFunction.addToRolePolicy(new PolicyStatement({
      actions: ['states:StartExecution'],
      resources: [stateMachine.stateMachineArn],
    }));


    const readScanConfigs = new lambda.Function(this, 'ReadScanConfigs', {
      runtime: lambda.Runtime.PYTHON_3_9,
      tracing: lambda.Tracing.ACTIVE,
      timeout: Duration.minutes(10),
      code: assetCode,
      handler: `${componentSubDirectoryInLambdaCode}/supported_configuration/scan_configurations.lambda_handler`,
      environment: {
        LOG_LEVEL: 'INFO',
        COMPONENT_TABLE: this.componentTable.tableName,
        POWERTOOLS_SERVICE_NAME: 'ReadScanConfigs',
        SOLUTION_VERSION: componentConfig.solutionVersion,
        STACK_ID: componentConfig.stackId,
        SEND_ANONYMOUS_DATA: componentConfig.sendAnonymousData
      }
    });
    this.componentTable.grantReadData(readScanConfigs);
    const scanConfigsResource = api.root.addResource('scan-configs');
    scanConfigsResource.addMethod('GET', new LambdaIntegration(readScanConfigs), {
      authorizationType: AuthorizationType.COGNITO,
      authorizer: {
        authorizerId: cognitoAuthenticationResources.authorizerFullAccess.ref
      },
    });
  }
}
