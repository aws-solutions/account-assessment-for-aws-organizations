// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {Construct} from "constructs";
import * as cdk from "aws-cdk-lib";
import {aws_cognito as cognito, CfnOutput, CfnParameter, CustomResource, Duration} from "aws-cdk-lib";
import {Mfa, OAuthScope, UserPool, UserPoolClient, UserPoolResourceServer} from "aws-cdk-lib/aws-cognito";
import {CfnAuthorizer} from "aws-cdk-lib/aws-apigateway";
import * as lambda from "aws-cdk-lib/aws-lambda";
import {AssetCode, Runtime} from "aws-cdk-lib/aws-lambda";
import {PolicyStatement} from "aws-cdk-lib/aws-iam";

type CognitoAuthenticationProps = {
  domainName: string,
  region: string,
  restApiId: string,
  emailTitle: string,
  emailSubject: string,
  cognitoDomainPrefix: string,
  multiFactorAuthentication: CfnParameter,
  userEmail: CfnParameter,
  assetCode: AssetCode,
};

export type CognitoAuthenticationResources = {
  userPoolClient: UserPoolClient;
  userPool: UserPool;
  authorizerFullAccess: CfnAuthorizer,
  oauthDomain: string
};

export class CognitoAuthenticator extends Construct {
  public readonly cognitoAuthenticationResources: CognitoAuthenticationResources;

  constructor(scope: Construct,
              id: string,
              {
                region,
                domainName,
                restApiId,
                emailTitle,
                emailSubject,
                cognitoDomainPrefix,
                multiFactorAuthentication,
                userEmail,
                assetCode
              }: CognitoAuthenticationProps) {
    super(scope, id);

    const createInvitationEmailBody = () => {
      return "<p>" + emailTitle + "</p>" +
        "<p>Here are your temporary login credentials for the WebUI: https://" + domainName + "</p>\n" +
        "<p>\n" +
        "Region: " + region + "<br />\n" +
        "Username: <strong>{username}</strong><br />\n" +
        "Temporary Password: <strong>{####}</strong>\n" +
        "</p>";
    }

    const domainLambda = new lambda.Function(this, 'DomainLambda', {
      runtime: Runtime.PYTHON_3_12,
      tracing: lambda.Tracing.ACTIVE,
      code: assetCode,
      handler: 'manage_cognito_domain/manage_cognito_domain.lambda_handler',
      timeout: cdk.Duration.minutes(5),
    });

    const userPool = new UserPool(this, 'FullAccessUsers', {
        signInAliases: {
          email: true
        },
        passwordPolicy: {
          minLength: 8,
          requireLowercase: true,
          requireUppercase: true,
          requireDigits: true,
          requireSymbols: true,
          tempPasswordValidity: Duration.days(7)
        },
        selfSignUpEnabled: false,
        userInvitation: {
          emailSubject: emailSubject,
          emailBody: createInvitationEmailBody()
        },
        mfa: multiFactorAuthentication.valueAsString as Mfa,
        mfaSecondFactor: {
          sms: false,
          otp: true,
        },
      }
    );
    domainLambda.addToRolePolicy(new PolicyStatement({
      actions: [
        'cognito-idp:CreateUserPoolDomain',
        'cognito-idp:DeleteUserPoolDomain',
      ],
      resources: [userPool.userPoolArn],
    }));

    new CustomResource(this, 'UserPoolDomainCustomResource', {
      serviceToken: domainLambda.functionArn,
      properties: {
        UserPoolId: userPool.userPoolId,
        DomainPrefix: cognitoDomainPrefix
      },
    });

    const apiAccessScope = {
      scopeName: 'api',
      scopeDescription: 'Access to solution API'
    };

    const resourceServer = new UserPoolResourceServer(this, 'ResourceServer', {
      identifier: 'account-assessment-api',
      userPoolResourceServerName: 'Resource Server representing the API Gateway of the solution',
      userPool: userPool,
      scopes: [apiAccessScope]
    });

    const cloudFrontUrl = `https://${domainName}/`;
    const userPoolClient = userPool.addClient('WebUIClient', {
      authFlows: {
        userSrp: true
      },
      oAuth: {
        callbackUrls: ["http://localhost:3000/", cloudFrontUrl],
        logoutUrls: ["http://localhost:3000/", cloudFrontUrl],
        flows: {
          authorizationCodeGrant: true,
        },
        scopes: [OAuthScope.OPENID, OAuthScope.PROFILE, OAuthScope.EMAIL, OAuthScope.COGNITO_ADMIN, OAuthScope.custom('account-assessment-api/api')]
      }
    });
    userPoolClient.node.addDependency(resourceServer)

    new CfnOutput(this, 'UserPoolIdOutput', {value: userPool.userPoolId});
    new CfnOutput(this, 'UserPoolClientIdOutput', {value: userPoolClient.userPoolClientId});

    const fullAccessGroupName = 'FullAccessGroup';
    const fullAccessGroup = new cognito.CfnUserPoolGroup(this, 'FullAccessGroup', {
      userPoolId: userPool.userPoolId,
      description: 'Provides unrestricted access to the RestApi',
      groupName: fullAccessGroupName,
    });

    const fullAccessPoolUser = new cognito.CfnUserPoolUser(this, 'InitialFullAccessUser', {
      userPoolId: userPool.userPoolId,
      username: userEmail.valueAsString,
      userAttributes: [{
        name: 'email_verified',
        value: 'true',
      }, {
        name: 'email',
        value: userEmail.valueAsString
      }],
    });
    const attachment = new cognito.CfnUserPoolUserToGroupAttachment(this, 'InitialFullAccessUserToGroupAttachment', {
      groupName: fullAccessGroupName,
      username: userEmail.valueAsString,
      userPoolId: userPool.userPoolId,
    });
    // Don't try to create attachment before user and group exist
    attachment.node.addDependency(fullAccessGroup, fullAccessPoolUser);

    const authorizerFullAccess = new CfnAuthorizer(this, 'FullAccessAuthorizer', {
      restApiId,
      name: 'FullAccessAuthorizer',
      type: 'COGNITO_USER_POOLS',
      identitySource: 'method.request.header.Authorization',
      providerArns: [userPool.userPoolArn],
    });
    const oauthDomain = `${cognitoDomainPrefix}.auth.${region}.amazoncognito.com`
    this.cognitoAuthenticationResources = {authorizerFullAccess, userPool, userPoolClient, oauthDomain};
  }
}