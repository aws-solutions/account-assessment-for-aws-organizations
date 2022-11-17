# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import os
import uuid
from logging import Logger
from typing import Optional, List

from assessment_runner.job_model import JobModel, JobCreateRequest, JobTaskFailureCreateRequest, JobMarkerModel
from aws.services.dynamodb import DynamoDB
from utils.api_gateway_lambda_handler import ClientException
from utils.base_repository import BaseRepository

PARTITION_KEY_JOBS = 'jobs'
PARTITION_KEY_JOB_MARKER = 'lastJobMarker'
PARTITION_KEY_TASK_FAILURES = 'taskFailures'


def sort_key_jobs(assessment_type: str, job_id: str):
    return f'{assessment_type}#{job_id}'


def sort_key_task_failure(job_id: str):
    return f'{job_id}#{uuid.uuid4().hex}'


class JobsRepository(BaseRepository):
    def __init__(self):
        super().__init__()
        self.logger = Logger(os.getenv('LOG_LEVEL'))
        self.dynamodb_jobs = DynamoDB(os.getenv('TABLE_JOBS'))

    def create_job(self, request: JobCreateRequest) -> JobModel:
        job_id = uuid.uuid4().hex
        new_job: JobModel = dict(
            request,
            PartitionKey=PARTITION_KEY_JOBS,
            SortKey=sort_key_jobs(request['AssessmentType'], job_id),
            JobId=job_id,
            ExpiresAt=self._calculate_expires_at()
        )
        self.dynamodb_jobs.put_item(new_job)
        return new_job

    def put_job(self, job: JobModel):
        self.dynamodb_jobs.put_item(job)

    def get_job(self, assessment_type: str, job_id: str) -> JobModel:
        try:
            return self.dynamodb_jobs.get_by_id(PARTITION_KEY_JOBS, assessment_type + '#' + job_id)
        except Exception as error:
            self.logger.error(error)
            self.logger.error(f"No job with assessmentType {assessment_type}, jobId {job_id}")
            raise ClientException("Job not found", f"No job with jobId {job_id}")

    def find_all_jobs(self) -> List[JobModel]:
        return self.dynamodb_jobs.find_items_by_partition_key(PARTITION_KEY_JOBS)

    def find_jobs_by_assessment_type(self, assessment_type: str) -> List[JobModel]:
        return self.dynamodb_jobs.query(PARTITION_KEY_JOBS, assessment_type)

    def put_last_job_marker(self, job_model: JobModel):
        active_job_marker: JobMarkerModel = {
            'PartitionKey': PARTITION_KEY_JOB_MARKER,
            'SortKey': job_model['AssessmentType'],
            'AssessmentType': job_model['AssessmentType'],
            'JobStatus': str(job_model['JobStatus']),
            'JobId': job_model['JobId'],
            'ExpiresAt': self._calculate_expires_at(),
        }
        self.dynamodb_jobs.put_item(active_job_marker)

        self.logger.debug(f'Stored last job as {job_model["JobId"]} {job_model["JobStatus"]}')
        return active_job_marker

    def get_last_job_marker(self, assessment_type: str) -> Optional[JobMarkerModel]:
        result = self.dynamodb_jobs.query(PARTITION_KEY_JOB_MARKER, assessment_type)
        if len(result) == 0:
            return None
        else:
            return result[0]

    def delete_last_job_marker(self, marker: JobMarkerModel):
        self.dynamodb_jobs.delete_item({
            'PartitionKey': PARTITION_KEY_JOB_MARKER,
            'SortKey': marker['SortKey']
        })

    def find_all_job_markers(self) -> List[JobMarkerModel]:
        return self.dynamodb_jobs.find_items_by_partition_key(PARTITION_KEY_JOB_MARKER)

    def delete_job(self, assessment_type, job_id):
        self.dynamodb_jobs.delete_item({
            'PartitionKey': PARTITION_KEY_JOBS,
            'SortKey': sort_key_jobs(assessment_type, job_id)
        })

    def create_job_task_failure(self, request: JobTaskFailureCreateRequest):
        new_failure = dict(
            **request,
            PartitionKey=PARTITION_KEY_TASK_FAILURES,
            SortKey=sort_key_task_failure(request["JobId"]),
            ExpiresAt=self._calculate_expires_at()
        )
        self.dynamodb_jobs.put_item(new_failure)
        self.logger.debug('Wrote task failure: ' + json.dumps(new_failure))

    def find_task_failures_by_job_id(self, job_id):
        return self.dynamodb_jobs.query(PARTITION_KEY_TASK_FAILURES, job_id)
