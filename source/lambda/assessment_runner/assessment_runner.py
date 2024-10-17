#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import os
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

from assessment_runner.job_model import JobModel, JobStatus, JobTaskFailureCreateRequest
from assessment_runner.jobs_repository import JobsRepository
from utils.api_gateway_lambda_handler import ClientException


class ScanStrategy(ABC):
    @abstractmethod
    def assessment_type(self) -> str: pass

    @abstractmethod
    def scan(self, job_id: str, request_body: Dict) -> List[Dict]: pass


class SynchronousScanStrategy(ScanStrategy):
    """A SynchronousScanStrategy has a write method, because it will do it's work synchronously and write the result
    to ddb immediately.
    In contrast, an (asynchronous) ScanStrategy does not have a write method, because it will trigger an asynchronous
    resource, e.g. Step Function, Message Queue or another Lambda Function. The current Lambda will terminate
    and leave it to the triggered asynchronous resource to write its result to ddb. The asynchronous resource needs
    to make sure to call finish_async_job when it is done doing it's work in order to register the job as finished."""

    @abstractmethod
    def write(self, items: List[Dict]): pass


class AssessmentRunner:
    def __init__(self, scan_strategy: ScanStrategy):
        self.logger = Logger(os.getenv('LOG_LEVEL'))
        self.scan_strategy = scan_strategy
        self.assessment_type = scan_strategy.assessment_type()
        self.job_repository = JobsRepository()

    def run_assessment(
            self,
            event: APIGatewayProxyEvent,
            _context: LambdaContext,
    ) -> JobModel:
        self._raise_if_active_job()

        new_job: JobModel = self._create_job_entry_in_ddb(event)
        try:
            items = self.scan_strategy.scan(new_job['JobId'], event.json_body if event.body else {})

            if isinstance(self.scan_strategy, SynchronousScanStrategy):
                self.scan_strategy.write(items)
                updated_job = self._finish_job(new_job, JobStatus.SUCCEEDED)
                return updated_job
            else:
                return new_job
        except Exception as e:
            self.logger.error('Failed to scan/write in Job ' + new_job['JobId'])
            self.logger.error(traceback.format_exc())
            self.logger.error(e)
            if isinstance(e, ClientException):
                new_job['Error'] = e.error + " " + e.message
            self._finish_job(new_job, JobStatus.FAILED)
            raise

    def _create_job_entry_in_ddb(self, event: APIGatewayProxyEvent) -> JobModel:

        new_job = self.job_repository.create_job({
            'AssessmentType': self.assessment_type,
            'StartedAt': datetime.now().isoformat(),
            'StartedBy': event.request_context.authorizer.claims['email'],
            'JobStatus': str(JobStatus.ACTIVE.value),
        })

        self.job_repository.put_last_job_marker(new_job)
        return new_job

    def _finish_job(self, job: JobModel, status: JobStatus) -> JobModel:
        updated_job: JobModel = dict(
            job,
            FinishedAt=(datetime.now().isoformat()),
            JobStatus=str(status.value),
        )

        self.job_repository.put_job(updated_job)
        self.job_repository.put_last_job_marker(updated_job)

        return updated_job

    def _raise_if_active_job(self):
        active_job: Optional[JobModel] = self.job_repository.get_last_job_marker(self.assessment_type)
        if active_job and active_job['JobStatus'] == str(JobStatus.ACTIVE.value):
            raise ClientException(
                'Scan running',
                'Cannot start another scan of type {0} while there is already a scan of this type running. '.format(
                    self.assessment_type)
            )


def write_task_failure(job_id, assessment_type, account_id, region, service_name, error):
    """Is called by an async job (e.g. Step Function) to document a failure in a single task of the job.
    The function finish_async_job will later check for such failures to determine if the whole job finished with issues
    or without issues."""
    job_repository = JobsRepository()

    job_failure: JobTaskFailureCreateRequest = {
        'AssessmentType': assessment_type,
        'JobId': job_id,
        'ServiceName': service_name,
        'AccountId': account_id,
        'Region': region,
        'FailedAt': datetime.now().isoformat(),
        'Error': error
    }
    job_repository.create_job_task_failure(job_failure)
