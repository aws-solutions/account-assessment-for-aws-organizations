import {Construct} from "constructs";
import {CloudFrontToS3} from "@aws-solutions-constructs/aws-cloudfront-s3";
import {CfnOutput, CfnParameter, Duration} from "aws-cdk-lib";
import {
  DistributionProps,
  HeadersFrameOption,
  HeadersReferrerPolicy,
  ResponseHeadersPolicy,
  ViewerProtocolPolicy
} from "aws-cdk-lib/aws-cloudfront";
import {S3Origin} from "aws-cdk-lib/aws-cloudfront-origins";
import * as defaults from '@aws-solutions-constructs/core';
import {IBucket} from "aws-cdk-lib/aws-s3";

type WebUIHostingProps = {
  region: string,
  namespace: CfnParameter,
};

export class WebUIHosting extends Construct {
  public readonly cloudFrontToS3: CloudFrontToS3;
  public readonly s3BucketInterface: IBucket;

  constructor(scope: Construct, id: string, {
    region,
    namespace
  }: WebUIHostingProps) {
    super(scope, id)

    const securityHeadersPolicy = new ResponseHeadersPolicy(this, 'ResponseHeadersPolicy', {
      responseHeadersPolicyName: `${namespace.valueAsString}-${region}-ResponseHeadersPolicy`,
      comment: 'Adds a set of recommended security headers',
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
    });

    const [s3BucketInterface] = defaults.buildS3Bucket(scope, {
      bucketProps: {},
      loggingBucketProps: {},
      logS3AccessLogs: true
    });
    this.s3BucketInterface = s3BucketInterface;

    this.cloudFrontToS3 = new CloudFrontToS3(scope, 'CloudFront',
      {
        existingBucketObj: s3BucketInterface,
        insertHttpSecurityHeaders: false,
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
          ],
          defaultBehavior: {
            origin: new S3Origin(this.s3BucketInterface),
            viewerProtocolPolicy: ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            responseHeadersPolicy: securityHeadersPolicy,

          }
        } as DistributionProps
      }
    );

    new CfnOutput(scope, 'WebUserInterfaceURL ', {
      value: `https://${this.cloudFrontToS3.cloudFrontWebDistribution.distributionDomainName}`
    });
  }

}
