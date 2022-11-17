# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import uuid
from os import getenv
from typing import Optional

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response, content_types
from aws_lambda_powertools.event_handler.exceptions import NotFoundError
from aws_lambda_powertools.utilities.typing import LambdaContext

from assessment_runner.job_model import JobDetails
from assessment_runner.jobs_service import JobsService
from utils.api_gateway_lambda_handler import ResultListWrapper, ClientException
from utils.decimal_json_encoder import DecimalJsonEncoder


def api_response_serializer(obj) -> str:
    return json.dumps(obj, cls=DecimalJsonEncoder)


app = APIGatewayRestResolver(serializer=api_response_serializer)
logger = Logger(getenv('LOG_LEVEL'))
tracer = Tracer()


@app.delete("/jobs/<assessment_type>/<job_id>", cors=True)
def delete_job(assessment_type: str, job_id: str):
    uuid.UUID(job_id)
    return JobsService().delete_job(assessment_type, job_id)


@app.get("/jobs/<assessment_type>/<job_id>", cors=True)
def read_job(assessment_type: str, job_id: str) -> JobDetails:
    uuid.UUID(job_id)
    return JobsService().read_job(assessment_type, job_id)


@app.get("/jobs", cors=True)
def read_jobs() -> ResultListWrapper:
    parameters = app.current_event.query_string_parameters
    selection: Optional[str] = parameters.get("selection") if parameters else None
    return JobsService().read_all_jobs(selection)


@app.not_found
def handle_not_found_errors(exc: NotFoundError) -> Response:
    logger.debug(f"Not found route: {app.current_event.path}")
    return Response(status_code=404, content_type=content_types.TEXT_PLAIN, body="Route not found.")


@app.exception_handler(ClientException)
def handle_client_exception(error: ClientException):
    logger.error(f"ClientException: {error}")

    return Response(
        status_code=error.status_code,
        content_type=content_types.APPLICATION_JSON,
        body=json.dumps({
            'Error': error.error,
            'Message': error.message
        }, cls=DecimalJsonEncoder)
    )


@app.exception_handler(ValueError)
def handle_client_exception(error: ValueError):
    logger.error(f"ValueError: {error}")

    return Response(
        status_code=400,
        content_type=content_types.APPLICATION_JSON,
        body=json.dumps({
            'Error': 'ValueError',
            'Message': error.args[0]
        }, cls=DecimalJsonEncoder)
    )


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
