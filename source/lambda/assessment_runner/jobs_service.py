#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os

from aws_lambda_powertools import Logger

from assessment_runner.job_model import JobModel, JobStatus, JobDetails
from assessment_runner.jobs_repository import JobsRepository
from aws.services.dynamodb import DynamoDB
from utils.api_gateway_lambda_handler import ClientException, ResultListWrapper


class JobsService:
    def __init__(self):
        self.logger = Logger(os.getenv('LOG_LEVEL'))
        self.repository = JobsRepository()

    def read_job(self, assessment_type: str, job_id: str) -> JobDetails:
        job = self.repository.get_job(assessment_type, job_id)
        task_failures = self.repository.find_task_failures_by_job_id(job_id)

        if assessment_type == 'POLICY_EXPLORER':
            findings = []  # policy explorer scan yields too many results to be returned
        else:
            findings_table = self._get_findings_table(assessment_type, job_id)

            findings = findings_table.find_items_by_secondary_index(
                index_name='JobId',
                key='JobId',
                index_value=job_id)
        return {
            'Job': job,
            'Findings': findings,
            'TaskFailures': task_failures
        }

    def _get_findings_table(self, assessment_type, job_id):
        env_variable_name = 'TABLE_' + assessment_type
        findings_table_name = os.getenv(env_variable_name)
        try:
            findings_table = DynamoDB(findings_table_name)
        except Exception as error:
            self.logger.error(error)
            raise ClientException("Access findings failed",
                                  f"Failed to access findings for {job_id} from table {findings_table_name}")
        return findings_table

    def read_all_jobs(self, selection: str) -> ResultListWrapper:
        if selection == 'latest':
            markers = self.repository.find_all_job_markers()
            jobs = list(self.repository.get_job(it['AssessmentType'], it['JobId']) for it in markers)
        else:
            jobs = self.repository.find_all_jobs()
        return {
            'Results': jobs
        }
