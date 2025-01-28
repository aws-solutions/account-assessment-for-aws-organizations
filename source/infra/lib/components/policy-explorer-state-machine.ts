import {
  DefinitionBody,
  Fail,
  JsonPath,
  Map,
  Pass,
  ProcessorMode,
  ProcessorType,
  StateMachine,
  Succeed,
  TaskInput,
} from "aws-cdk-lib/aws-stepfunctions";
import { LambdaInvoke } from "aws-cdk-lib/aws-stepfunctions-tasks";
import { Construct } from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { CfnPolicy } from "aws-cdk-lib/aws-iam";
import { addCfnSuppressRules } from "@aws-solutions-constructs/core";

export function createStateMachine(
  scope: Construct,
  stateMachineName: string,
  validateAccountAccessFunction: lambda.Function,
  scanServicePerSpokeAccountFunction: lambda.Function,
  finishAsyncJob: lambda.Function
): StateMachine {
  const {
    scanServicePerAccountProps,
    taskCompleteProps,
    serviceIteratorProps,
    accountValidationProps,
    accountIteratorProps,
    finishJobProps,
    failedJobProps,
  } = stateMachineTaskProps(
    scanServicePerSpokeAccountFunction,
    validateAccountAccessFunction,
    finishAsyncJob
  );

  const setJobStatusToFailed = new LambdaInvoke(
    scope,
    "FailJob",
    failedJobProps
  ).next(new Fail(scope, "Failed"));

  const definitionBody = DefinitionBody.fromChainable(
    new Map(scope, "AccountIterator", accountIteratorProps)
      .itemProcessor(
        new LambdaInvoke(
          scope,
          "AccountValidation",
          accountValidationProps
        ).next(
          new Map(scope, "ServiceIterator", serviceIteratorProps).itemProcessor(
            new LambdaInvoke(
              scope,
              "ScanServicePerAccount",
              scanServicePerAccountProps
            ).next(new Pass(scope, "TaskComplete", taskCompleteProps))
          , {mode: ProcessorMode.INLINE, executionType: ProcessorType.STANDARD})
        )
      , {mode: ProcessorMode.DISTRIBUTED, executionType: ProcessorType.STANDARD})
      .addCatch(setJobStatusToFailed, { resultPath: "$.Error" })
      .next(new LambdaInvoke(scope, "FinishJob", finishJobProps))
      .next(new Succeed(scope, "Success"))
  );

  const stateMachine = new StateMachine(scope, "ScanAllSpokeAccounts", {
    definitionBody: definitionBody,
    tracingEnabled: true,
    stateMachineName: stateMachineName,
  });
  const cfnPolicy = stateMachine.role.node
    .findChild("DefaultPolicy")
    .node.findChild("Resource") as CfnPolicy;
  cfnPolicy &&
    addCfnSuppressRules(cfnPolicy, [
      {
        id: "W12",
        reason:
          "Resource * is necessary for xray:PutTraceSegments and xray:PutTelemetryRecords.",
      },
    ]);
  return stateMachine;
}

function stateMachineTaskProps(
  scanServicePerSpokeAccountFunction: lambda.Function,
  validateAccountAccessFunction: lambda.Function,
  finishAsyncJob: lambda.Function
) {
  const accountIteratorProps = {
    maxConcurrency: 10,
    inputPath: "$",
    itemsPath: JsonPath.stringAt("$.Scan.AccountIds"),
    parameters: {
      "AccountId.$": "$$.Map.Item.Value",
      "ServiceNames.$": "$.Scan.ServiceNames",
      "JobId.$": "$.JobId",
    },
    resultPath: "$.ExecutionResults",
  };
  
  const accountValidationProps = {
    lambdaFunction: validateAccountAccessFunction,
    resultSelector: {
      "ServicesToScanForAccount.$": "$.Payload.ServicesToScanForAccount",
      "Status.$": "$.Payload.Validation",
      "StatusCode.$": "$.StatusCode",
      "RequestId.$": "$.SdkResponseMetadata.RequestId",
      "Regions.$": "$.Payload.Regions",
    },
    resultPath: "$.ValidationResult",
    retryOnServiceExceptions: true,
  };

  const serviceIteratorProps = {
    maxConcurrency: 10,
    itemsPath: JsonPath.stringAt("$.ValidationResult.ServicesToScanForAccount"),
    parameters: {
      "ServiceName.$": "$$.Map.Item.Value",
      "AccountId.$": "$.AccountId",
      "Regions.$": "$.ValidationResult.Regions",
      "JobId.$": "$.JobId",
    },
  };

  const scanServicePerAccountProps = {
    lambdaFunction: scanServicePerSpokeAccountFunction,
    resultSelector: {
      "Status.$": "$.Payload",
      "StatusCode.$": "$.StatusCode",
      "RequestId.$": "$.SdkResponseMetadata.RequestId",
    },
    retryOnServiceExceptions: true,
  };

  const taskCompleteProps = {
    parameters: {
      "StartTime.$": "$$.Execution.StartTime",
      "ExecutionName.$": "$$.Execution.Name",
    },
  };

  const finishJobProps = {
    lambdaFunction: finishAsyncJob,
    payload: TaskInput.fromObject({
      AssessmentType: "POLICY_EXPLORER",
      Result: "SUCCEEDED",
      JobId: JsonPath.stringAt("$.JobId"),
    }),
  };

  const failedJobProps = {
    lambdaFunction: finishAsyncJob,
    payload: TaskInput.fromObject({
      AssessmentType: "POLICY_EXPLORER",
      Result: "FAILED",
      JobId: JsonPath.stringAt("$.JobId"),
      Error: JsonPath.stringAt("$.Error"),
    }),
  };

  return {
    scanServicePerAccountProps,
    taskCompleteProps,
    serviceIteratorProps,
    accountValidationProps,
    accountIteratorProps,
    finishJobProps,
    failedJobProps,
  };
}
