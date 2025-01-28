#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from os import getenv

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from assessment_runner.job_model import JobModel, JobStatus
from assessment_runner.jobs_repository import JobsRepository

logger = Logger(getenv('LOG_LEVEL'))
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(payload: dict, context: LambdaContext):

    assessment_type = payload['AssessmentType']
    result = payload['Result']
    job_id = payload['JobId']

    logger.info(f'Finished scan with status {result}, updating job entry')

    return FinishScanForResourceBasedPolicies().finish(assessment_type, job_id, result)


class FinishScanForResourceBasedPolicies:
    def __init__(self):
        self.job_repository = JobsRepository()

    def finish(self, assessment_type: str, job_id: str, result: str = None):
        status = JobStatus.SUCCEEDED
        task_failures = self.job_repository.find_task_failures_by_job_id(job_id)
        if result == "FAILED":
            status = JobStatus.FAILED
        elif len(task_failures) > 0:
            status = JobStatus.SUCCEEDED_WITH_FAILED_TASKS

        job = self.job_repository.get_job(assessment_type, job_id)

        updated_job: JobModel = dict(
            job,
            FinishedAt=(datetime.now().isoformat()),
            JobStatus=str(status.value),
        )

        self.job_repository.put_job(updated_job)
        self.job_repository.put_last_job_marker(updated_job)

        return {
            "Status": str(status.value),
        }
