// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {Construct} from "constructs";
import {CloudFrontToS3} from "@aws-solutions-constructs/aws-cloudfront-s3";
import {CfnOutput, CfnParameter, Duration, Fn} from "aws-cdk-lib";
import {HeadersFrameOption, HeadersReferrerPolicy,} from "aws-cdk-lib/aws-cloudfront";
import {IBucket} from "aws-cdk-lib/aws-s3";


export class WebUIHosting extends Construct {
  public readonly cloudFrontToS3: CloudFrontToS3;
  public readonly s3BucketInterface: IBucket

  constructor(scope: Construct, id: string, {namespace}: { namespace: CfnParameter }) {
    super(scope, id)

    this.cloudFrontToS3 = new CloudFrontToS3(scope, 'CloudFront',
      {
        insertHttpSecurityHeaders: false,
        responseHeadersPolicyProps: {
          responseHeadersPolicyName: Fn.join('-', [
            'AccountAssessmentHeaders',
            id,
            namespace.valueAsString,
            Fn.ref('AWS::Region')
          ]),
          comment: 'Adds a set of recommended security headers',
          customHeadersBehavior: {
            customHeaders: [
              {
                header: 'Cache-Control',
                value: 'no-store, no-cache',
                override: true,
              },
              {
                header: 'Pragma',
                value: 'no-cache',
                override: true,
              },
            ],
          },
          securityHeadersBehavior: {
            contentSecurityPolicy: {
              contentSecurityPolicy: "upgrade-insecure-requests; default-src 'none'; manifest-src 'self'; img-src 'self'; font-src data:; connect-src 'self' https:; script-src 'self'; style-src https:; base-uri 'none'; frame-ancestors 'none';",
              override: true
            },
            contentTypeOptions: {override: true},
            frameOptions: {frameOption: HeadersFrameOption.DENY, override: true},
            referrerPolicy: {referrerPolicy: HeadersReferrerPolicy.SAME_ORIGIN, override: true},
            strictTransportSecurity: {
              accessControlMaxAge: Duration.days(30),
              includeSubdomains: true,
              override: true,
              preload: true
            },
          },
        },
        cloudFrontDistributionProps: {
          errorResponses: [
            {
              httpStatus: 403,
              ttl: Duration.seconds(300),
              responseHttpStatus: 200,
              responsePagePath: '/index.html'
            },
            {
              httpStatus: 404,
              ttl: Duration.seconds(300),
              responseHttpStatus: 200,
              responsePagePath: '/index.html'
            },
            {
              httpStatus: 400,
              ttl: Duration.seconds(300),
              responseHttpStatus: 200,
              responsePagePath: '/index.html'
            }
          ]
        }
      }
    );
    this.s3BucketInterface = this.cloudFrontToS3.s3BucketInterface
    new CfnOutput(scope, 'WebUserInterfaceURL ', {
      value: `https://${this.cloudFrontToS3.cloudFrontWebDistribution.distributionDomainName}`
    });
  }

}
