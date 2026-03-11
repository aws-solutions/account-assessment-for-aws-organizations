"""
Account Assessment Dashboard — Local FastAPI server.
Proxies Lambda invocations and DynamoDB reads through your AWS SSO session.

Usage:
    pip install -r requirements.txt
    python server.py
"""

import json
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Optional

import boto3
import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse


class DecimalEncoder(json.JSONEncoder):
    """Handle DynamoDB Decimal values."""
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o == int(o) else float(o)
        return super().default(o)


def decimal_safe(obj):
    """Recursively convert Decimals in dicts/lists."""
    if isinstance(obj, list):
        return [decimal_safe(i) for i in obj]
    if isinstance(obj, dict):
        return {k: decimal_safe(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return int(obj) if obj == int(obj) else float(obj)
    return obj

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
AWS_PROFILE = "gusto-account-migration-assessment"
AWS_REGION = "us-east-2"
CALLER_EMAIL = "julien.covington@gusto.com"

LAMBDA_FUNCTIONS = {
    "delegated-admins": "account-migration-hub-sta-DelegatedAdminsStartScan-bAGeDvDHRMPe",
    "trusted-access": "account-migration-hub-sta-TrustedAccessStartScan70-uD0zbTN7gprN",
    "policy-explorer": "account-migration-hub-sta-PolicyExplorerStartScan0-Ow6cNXEU6DjE",
    "spoke-validate": "account-migration-hub-sta-PolicyExplorerValidateSp-x4ikyVzXrjyT",
    "spoke-resource": "account-migration-hub-sta-PolicyExplorerPolicyExpl-FVbWOjEsnOgp",
}

DYNAMO_TABLES = {
    "delegated-admins": "account-migration-hub-stack-DelegatedAdminsTable29E80916-4UEB6UWKPK2I",
    "trusted-access": "account-migration-hub-stack-TrustedAccessTable495B447A-YP1EH9XA20IK",
    "policy-explorer": "account-migration-hub-stack-PolicyExplorerTable3E6DD7C7-17PYV14ITAJ47",
    "jobs": "account-migration-hub-stack-JobHistoryTableE4B293DD-LSNOWD22KPNM",
}

ALL_SPOKE_SERVICES = [
    "s3", "iam", "sqs", "lambda_layer", "sns", "kms", "efs",
    "secretsmanager", "codeartifact", "codebuild", "mediastore", "glue",
    "ses", "opensearch", "glacier", "ecr", "backup",
    "eventbridge_schemas", "eventbridge", "acm_pca",
    "serverless_application", "ram", "lex", "cloudwatch_logs",
    "apigateway", "lambda_function", "iot",
]

# ---------------------------------------------------------------------------
# AWS clients (lazy-init so import doesn't fail without creds)
# ---------------------------------------------------------------------------
_session: Optional[boto3.Session] = None


def session() -> boto3.Session:
    global _session
    if _session is None:
        _session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    return _session


def lambda_client():
    return session().client("lambda")


def dynamo_resource():
    return session().resource("dynamodb")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _api_gw_payload() -> dict:
    """Standard API-Gateway-like event payload for hub Lambdas."""
    return {
        "requestContext": {
            "authorizer": {"claims": {"email": CALLER_EMAIL}}
        },
        "body": None,
    }


def _invoke_lambda(function_name: str, payload: dict) -> dict:
    resp = lambda_client().invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode(),
    )
    raw = resp["Payload"].read().decode()
    if not raw or raw == "null":
        return {"status": "ok", "result": None}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def _scan_table(table_name: str, filter_expr=None, expr_values=None, limit=500) -> list:
    table = dynamo_resource().Table(table_name)
    kwargs: dict = {"Limit": limit}
    if filter_expr:
        kwargs["FilterExpression"] = filter_expr
        kwargs["ExpressionAttributeValues"] = expr_values or {}
    items = []
    while True:
        resp = table.scan(**kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp or len(items) >= limit:
            break
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    return decimal_safe(items[:limit])


def _query_table(table_name: str, pk_name: str, pk_value: str, limit=500) -> list:
    table = dynamo_resource().Table(table_name)
    kwargs = {
        "KeyConditionExpression": boto3.dynamodb.conditions.Key(pk_name).eq(pk_value),
        "Limit": limit,
    }
    items = []
    while True:
        resp = table.query(**kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp or len(items) >= limit:
            break
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    return decimal_safe(items[:limit])


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Account Assessment Dashboard")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Frontend ----
HTML_PATH = Path(__file__).parent / "index.html"


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return HTML_PATH.read_text()


# ---- Scan endpoints ----

@app.post("/api/scan/delegated-admins")
async def scan_delegated_admins():
    return _invoke_lambda(LAMBDA_FUNCTIONS["delegated-admins"], _api_gw_payload())


@app.post("/api/scan/trusted-access")
async def scan_trusted_access():
    return _invoke_lambda(LAMBDA_FUNCTIONS["trusted-access"], _api_gw_payload())


@app.post("/api/scan/policy-explorer")
async def scan_policy_explorer():
    return _invoke_lambda(LAMBDA_FUNCTIONS["policy-explorer"], _api_gw_payload())


@app.post("/api/scan/spoke-validate")
async def scan_spoke_validate(account_id: str = Query(...)):
    job_id = str(uuid.uuid4().hex)
    payload = {
        "AccountId": account_id,
        "ServiceNames": ALL_SPOKE_SERVICES,
        "JobId": job_id,
    }
    result = _invoke_lambda(LAMBDA_FUNCTIONS["spoke-validate"], payload)
    result["JobId"] = job_id
    return result


@app.post("/api/scan/spoke-resource")
async def scan_spoke_resource(
    account_id: str = Query(...),
    service: str = Query(...),
    regions: str = Query("us-east-2,us-west-2"),
):
    job_id = str(uuid.uuid4().hex)
    payload = {
        "AccountId": account_id,
        "ServiceName": service,
        "Regions": [r.strip() for r in regions.split(",")],
        "JobId": job_id,
    }
    result = _invoke_lambda(LAMBDA_FUNCTIONS["spoke-resource"], payload)
    return {"status": "ok", "JobId": job_id, "result": result}


@app.post("/api/scan/spoke-all")
async def scan_spoke_all(
    account_id: str = Query(...),
    regions: str = Query("us-east-2,us-west-2"),
):
    """Validate then scan all services for a spoke account."""
    region_list = [r.strip() for r in regions.split(",")]
    job_id = str(uuid.uuid4().hex)

    # Validate first
    validate_payload = {
        "AccountId": account_id,
        "ServiceNames": ALL_SPOKE_SERVICES,
        "JobId": job_id,
    }
    validation = _invoke_lambda(LAMBDA_FUNCTIONS["spoke-validate"], validate_payload)

    if validation.get("Validation") != "SUCCEEDED":
        return {"status": "failed", "validation": validation}

    services_to_scan = validation.get("ServicesToScanForAccount", ALL_SPOKE_SERVICES)
    available_regions = validation.get("Regions", region_list)
    scan_regions = list(set(region_list) & set(available_regions)) or region_list

    results = []
    for svc in services_to_scan:
        svc_job = str(uuid.uuid4().hex)
        payload = {
            "AccountId": account_id,
            "ServiceName": svc,
            "Regions": scan_regions,
            "JobId": svc_job,
        }
        try:
            r = _invoke_lambda(LAMBDA_FUNCTIONS["spoke-resource"], payload)
            results.append({"service": svc, "status": "ok", "JobId": svc_job})
        except Exception as e:
            results.append({"service": svc, "status": "error", "error": str(e)})

    return {
        "status": "ok",
        "validation": validation,
        "scans": results,
        "totalServices": len(services_to_scan),
    }


# ---- Results endpoints ----

@app.get("/api/results/delegated-admins")
async def results_delegated_admins():
    items = _scan_table(DYNAMO_TABLES["delegated-admins"])
    return {"count": len(items), "items": items}


@app.get("/api/results/trusted-access")
async def results_trusted_access():
    items = _scan_table(DYNAMO_TABLES["trusted-access"])
    return {"count": len(items), "items": items}


@app.get("/api/results/policy-explorer")
async def results_policy_explorer(
    account_id: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    effect: Optional[str] = Query(None),
    limit: int = Query(500),
):
    filters = []
    values = {}

    if account_id:
        filters.append("AccountId = :acct")
        values[":acct"] = account_id
    if region:
        filters.append("Region = :rgn")
        values[":rgn"] = region
    if service:
        filters.append("Service = :svc")
        values[":svc"] = service
    if effect:
        filters.append("Effect = :eff")
        values[":eff"] = effect

    filter_expr = " AND ".join(filters) if filters else None
    items = _scan_table(
        DYNAMO_TABLES["policy-explorer"],
        filter_expr=filter_expr,
        expr_values=values if values else None,
        limit=limit,
    )
    return {"count": len(items), "items": items}


@app.get("/api/results/jobs")
async def results_jobs():
    from boto3.dynamodb.conditions import Key
    table = dynamo_resource().Table(DYNAMO_TABLES["jobs"])
    resp = table.query(KeyConditionExpression=Key("PartitionKey").eq("jobs"))
    items = resp.get("Items", [])
    return {"count": len(items), "items": items}


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n  Account Assessment Dashboard")
    print("  http://localhost:8787\n")
    uvicorn.run(app, host="0.0.0.0", port=8787)
