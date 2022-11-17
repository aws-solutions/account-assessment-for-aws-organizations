# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from os import getenv

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from assessment_runner.job_model import JobModel, JobStatus
from assessment_runner.jobs_repository import JobsRepository
from metrics.solution_metrics import SolutionMetrics
from resource_based_policy.resource_based_policies_repository import ResourceBasedPoliciesRepository

tracer = Tracer()


@tracer.capture_lambda_handler
def lambda_handler(payload: dict, context: LambdaContext):
    logger = Logger(getenv('LOG_LEVEL'))
    logger.info(f"Payload: {str(payload)}")
    logger.info(f"Context: {str(context)}")

    assessment_type = payload['AssessmentType']
    result = payload['Result']
    job_id = payload['JobId']

    return FinishScanForResourceBasedPolicies().finish(assessment_type, job_id, result)


class FinishScanForResourceBasedPolicies:
    def __init__(self):
        self.job_repository = JobsRepository()
        self.resource_based_policy_repository = ResourceBasedPoliciesRepository()

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

        findings = self.resource_based_policy_repository.find_all_by_job_id(job_id)
        SolutionMetrics().send_metrics(job['AssessmentType'], findings)

        return {
            "Status": str(status.value),
        }
