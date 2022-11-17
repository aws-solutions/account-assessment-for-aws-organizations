import {Construct} from "constructs";
import {CfnOutput, CfnParameter} from "aws-cdk-lib";
import {LogGroup} from "aws-cdk-lib/aws-logs";
import {AccessLogFormat, LogGroupLogDestination, RestApi} from "aws-cdk-lib/aws-apigateway";
import {CfnIPSet, CfnWebACL, CfnWebACLAssociation} from "aws-cdk-lib/aws-wafv2";
import {wrapManagedRuleSet} from "@aws-solutions-constructs/core";

type ApiProps = {
  region: string,
  allowListedIPRanges: CfnParameter,
  namespace: CfnParameter,
};

export class Api extends Construct {
  public readonly restApi: RestApi;
  public readonly apiGatewayUrl: string;

  constructor(scope: Construct, id: string, {region, allowListedIPRanges, namespace}: ApiProps) {
    super(scope, id);

    const prodLogGroup = new LogGroup(this, "ProdLogs");
    const api = new RestApi(this, 'AccountAssessmentForAWSOrganisationsApi', {
      restApiName: `AccountAssessmentForAWSOrganisationsApi-${namespace.valueAsString}`,
      deployOptions: {
        stageName: 'prod',
        accessLogDestination: new LogGroupLogDestination(prodLogGroup),
        accessLogFormat: AccessLogFormat.jsonWithStandardFields(),
        tracingEnabled: true
      },
      defaultCorsPreflightOptions: {
        allowOrigins: ['*'],
        allowMethods: ['*'],
        allowCredentials: false,
        allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key', 'X-Amz-Security-Token', 'X-Amz-User-Agent']
      },
    });

    const ipSet = new CfnIPSet(this, 'IPSet', {
      addresses: allowListedIPRanges.valueAsList.map(it => it.trim()),
      ipAddressVersion: 'IPV4',
      scope: 'REGIONAL',
    });

    const cfnWebACL = new CfnWebACL(scope, `WebACL`, {
      defaultAction: {block: {}},
      scope: 'REGIONAL',
      visibilityConfig: {
        cloudWatchMetricsEnabled: true,
        metricName: "AccountAssessmentWebAclMetrics",
        sampledRequestsEnabled: true,
      },
      rules: [{
        name: "AllowlistRule",
        priority: 0,
        action: {allow: {}},
        visibilityConfig: {
          cloudWatchMetricsEnabled: true,
          metricName: "AccountAssessment-AllowlistMetric",
          sampledRequestsEnabled: true,
        },
        statement: {
          ipSetReferenceStatement: {
            arn: ipSet.attrArn,
          },
        },
      },
        wrapManagedRuleSet("AWSManagedRulesBotControlRuleSet", "AWS", 1),
        wrapManagedRuleSet("AWSManagedRulesKnownBadInputsRuleSet", "AWS", 2),
        wrapManagedRuleSet("AWSManagedRulesCommonRuleSet", "AWS", 3),
        wrapManagedRuleSet("AWSManagedRulesAnonymousIpList", "AWS", 4),
        wrapManagedRuleSet("AWSManagedRulesAmazonIpReputationList", "AWS", 5),
        wrapManagedRuleSet("AWSManagedRulesAdminProtectionRuleSet", "AWS", 6),
        wrapManagedRuleSet("AWSManagedRulesSQLiRuleSet", "AWS", 7)
      ]
    });

    new CfnWebACLAssociation(this, 'MyCfnWebACLAssociation', {
      resourceArn: api.deploymentStage.stageArn,
      webAclArn: cfnWebACL.attrArn,
    });

    const apiGatewayUrl = `https://${api.restApiId}.execute-api.${region}.amazonaws.com/prod`;
    new CfnOutput(this, 'ApiGatewayURL', {
      value: apiGatewayUrl,
    });

    this.restApi = api;
    this.apiGatewayUrl = apiGatewayUrl;
  }

}
