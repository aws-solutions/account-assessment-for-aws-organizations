#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import json
import logging
from os import getenv

import cfnresponse
from aws_lambda_powertools import Logger, Tracer

from aws.services.s3 import S3

logger = Logger(getenv('LOG_LEVEL'))
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=False)
def lambda_handler(event, context):

    try:
        if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
            WebUIDeployer().deploy()
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
    except Exception as err:
        logger.error(err)
        cfnresponse.send(event, context, cfnresponse.FAILED, "An error occurred")


class WebUIDeployer:
    """Deploys the solution WebUI web application to an S3 bucket"""

    def __init__(self, **kwargs):
        self.logger = Logger(getenv('LOG_LEVEL'))
        self.s3 = S3(**kwargs)

    def deploy(self):
        """
        To deploy the solution console,
        * copy all files from source bucket that begin with /solution-name/version/webui to target bucket
        * create aws-exports.json in target bucket
        As opposed to regular frontend projects, the configuration is not known at build time
        because URLs and IDs only get created at deploy time.
        For that reason, aws-exports.json cannot be included in the build
        but has to be created dynamically at deploy time.
        """
        config = json.loads(getenv("CONFIG"))
        self.logger.info(config)
        self._copy_ui_files_to_console_bucket(config)
        self._create_config_file(config)

    def _create_config_file(self, config):
        self.logger.info("Reading awsExports")
        exports = config.get("awsExports")
        self.logger.info(exports)

        webui_bucket = config.get("WebUIBucket")
        self.logger.info("Creating aws-exports-generated.json in " + webui_bucket)
        self.s3.write_json_as_file(webui_bucket, "aws-exports-generated.json", exports)

    def _copy_ui_files_to_console_bucket(self, config):
        webui_bucket_name = config.get("WebUIBucket")
        source_bucket_name = config.get("SrcBucket")
        key_prefix = config.get("SrcPath")

        config_json = self.s3.read_json_file(source_bucket_name, key_prefix + 'webui-manifest.json')
        web_ui_file_names = config_json["files"]

        self.logger.info(
            "Deploying files from bucket " + source_bucket_name + ", path " + key_prefix + " to " + webui_bucket_name)

        for file_name in web_ui_file_names:
            self.s3.copy_file(source_bucket_name, webui_bucket_name, key_prefix, '', file_name)

        self.logger.info("WebUI assets copied successfully")
