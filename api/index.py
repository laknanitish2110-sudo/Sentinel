"""
Vercel Serverless Function entry point for Sentinel API (/api/*).
Provides WSGI application entrypoint 'app' compatible with @vercel/python runtime.
"""
import sys
import os
import json
from typing import Dict, Any, Optional

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem
from sentinel.api import SentinelCitizenAPI
from sentinel.vision.construction_adapter import ConstructionPerceptionAdapter

DEMO_PROJECT_WARD7_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
DEMO_PROJECT_WARD8_ID = "b1ffcd00-8d1c-5fg9-cc7e-7cc0ce491b22"

db_instance: Optional[SentinelDB] = None
api_instance: Optional[SentinelCitizenAPI] = None


def init_demo_db():
    global db_instance, api_instance
    if db_instance is not None and api_instance is not None:
        return

    db_instance = SentinelDB(":memory:")

    # Project 1: Ward 7
    p1 = Project(
        id=DEMO_PROJECT_WARD7_ID,
        code="DEMO-WARD7-DRAIN-2026",
        name="Ward 7 Stormwater Drainage Improvement [DEMO DATA]",
        description="Construction of RCC storm water drain and laying of 400m main drainage line along Ward 7 primary arterial road.",
        sanctioned_amount=1800000.0,
        released_amount=720000.0,
        currency="INR",
        location_name="Ward 7 Arterial Corridor, Zone 3",
        status="UNDER_AUDIT",
        metadata={"is_demo_data": True}
    )
    db_instance.save_project(p1)

    c1_1 = Claim(
        id="c1-ra2", project_id=p1.id, claim_ref="CLAIM-WARD7-RA-02", claimed_by="Apex Infra Works Ltd",
        claim_type="COMPLETION_PERCENTAGE", description="Contractor submission for 2nd RA Bill claiming 80% completion.",
        claimed_value=80.0, unit="percent", claim_date="2026-09-15"
    )
    c1_2 = Claim(
        id="c2-pipe400", project_id=p1.id, claim_ref="CLAIM-WARD7-PIPE-400M", claimed_by="Apex Infra Works Ltd",
        claim_type="PHYSICAL_QUANTITY", description="Contractor report asserting full installation of 400 meters of 600mm RCC hume pipes.",
        claimed_value=400.0, unit="meters", claim_date="2026-09-15"
    )
    db_instance.save_claim(c1_1)
    db_instance.save_claim(c1_2)

    e1_1 = EvidenceItem(
        id="e1-mb", project_id=p1.id, claim_id=c1_2.id, source_type="MB_RECORD", source_id="MB-BOOK-402/PAGE-18",
        observation="Junior Engineer Measurement Book entry certifying 400m of pipe excavation and laying completed.",
        value=400.0, unit="meters", timestamp="2026-09-14", location={"text": "Ward 7 Main Stretch"},
        confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
    )
    e1_2 = EvidenceItem(
        id="e2-photo", project_id=p1.id, claim_id=c1_2.id, source_type="PHYSICAL_INSPECTION", source_id="INSP-2026-W7-009",
        observation="Independent site audit photo inspection verified only 180 meters of pipe laid inside active trench.",
        value=180.0, unit="meters", timestamp="2026-09-18", location={"address": "Ward 7 Trench Section B"},
        confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
    )
    e1_3 = EvidenceItem(
        id="e3-inv", project_id=p1.id, claim_id=c1_2.id, source_type="INVOICE", source_id="INV-SOUTHERN-CONCRETE-9941",
        observation="Invoice from Southern Concrete Products confirming procurement and delivery of 400m of RCC hume pipes to site.",
        value=400.0, unit="meters", timestamp="2026-09-02", location={"delivery": "Ward 7 Staging Yard"},
        confidence=0.98, reliability="HIGH", relationship="NEUTRAL", metadata={"invoice_amount": 480000.0}
    )
    e1_4 = EvidenceItem(
        id="e4-bank", project_id=p1.id, claim_id=c1_1.id, source_type="BANK_STATEMENT", source_id="TREASURY-DISBURSEMENT-MISSING-02",
        observation="Treasury records confirm Tranche 1 release (₹7,20,000), but official Bank Clearance Certificate for second claimed tranche is unverified/absent.",
        value=720000.0, unit="INR", timestamp="2026-08-10", location=None,
        confidence=0.50, reliability="UNVERIFIED", relationship="INSUFFICIENT"
    )
    db_instance.save_evidence(e1_1)
    db_instance.save_evidence(e1_2)
    db_instance.save_evidence(e1_3)
    db_instance.save_evidence(e1_4)

    # Construction perception adapter
    adapter = ConstructionPerceptionAdapter(db=db_instance, confidence_threshold=0.25)
    sample_img = os.path.join(os.path.dirname(__file__), "..", "data", "vision_eval_real", "real_eval_02_construction_works_osaka.jpg")
    if os.path.exists(sample_img):
        adapter.detect_and_adapt(
            image_path=sample_img,
            project_id=p1.id,
            claim=c1_2,
            source_evidence_id="evi_osaka_real_ward7",
            location_override={"latitude": 12.9720, "longitude": 77.5950, "address": "Ward 7 Sector B"},
            timestamp_override="2026-09-18T10:30:00Z"
        )

    # Project 2: Ward 8
    p2 = Project(
        id=DEMO_PROJECT_WARD8_ID,
        code="DEMO-WARD8-DRAIN-2026",
        name="Ward 8 Drainage Extension [SECOND CASE]",
        description="Extension of 500m underground storm drain along Ward 8 commercial corridor.",
        sanctioned_amount=2500000.0,
        released_amount=1000000.0,
        currency="INR",
        location_name="Ward 8 Corridor, Zone 3",
        status="UNDER_AUDIT",
        metadata={"is_demo_data": True}
    )
    db_instance.save_project(p2)

    c2_1 = Claim(
        id="c2-w8-pipe500", project_id=p2.id, claim_ref="CLAIM-WARD8-PIPE-500M", claimed_by="Apex Infra Works Ltd",
        claim_type="PHYSICAL_QUANTITY", description="Contractor report asserting installation of 500 meters of RCC pipes.",
        claimed_value=500.0, unit="meters", claim_date="2026-09-20"
    )
    db_instance.save_claim(c2_1)

    e2_1 = EvidenceItem(
        id="e2-mb505", project_id=p2.id, claim_id=c2_1.id, source_type="MB_RECORD", source_id="MB-BOOK-505/PAGE-12",
        observation="Junior Engineer Measurement Book entry certifying 500m of pipe laying completed.",
        value=500.0, unit="meters", timestamp="2026-09-19", location={"text": "Ward 8 Main Road"},
        confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
    )
    e2_2 = EvidenceItem(
        id="e2-photo220", project_id=p2.id, claim_id=c2_1.id, source_type="PHYSICAL_INSPECTION", source_id="INSP-2026-W8-012",
        observation="Site photo inspection verified 220 meters visible in open trench.",
        value=220.0, unit="meters", timestamp="2026-09-21", location={"address": "Ward 8 Trench Section A"},
        confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
    )
    db_instance.save_evidence(e2_1)
    db_instance.save_evidence(e2_2)

    api_instance = SentinelCitizenAPI(db_instance)


def app(environ, start_response):
    """Standard WSGI entrypoint for Vercel Python Serverless Function."""
    init_demo_db()

    path = environ.get("PATH_INFO", "")
    query_string = environ.get("QUERY_STRING", "")
    method = environ.get("REQUEST_METHOD", "GET").upper()

    if method == "OPTIONS":
        headers = [
            ("Content-Type", "application/json"),
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type")
        ]
        start_response("200 OK", headers)
        return [b""]

    # Read request body if POST
    content_length = 0
    try:
        content_length = int(environ.get("CONTENT_LENGTH", 0) or 0)
    except Exception:
        content_length = 0

    body = {}
    if content_length > 0 and method == "POST":
        try:
            raw_body = environ["wsgi.input"].read(content_length).decode("utf-8")
            body = json.loads(raw_body)
        except Exception:
            body = {}

    project_id = DEMO_PROJECT_WARD7_ID
    if "project_id=" in query_string:
        project_id = query_string.split("project_id=")[-1].split("&")[0]
    elif "project_id=" in path:
        project_id = path.split("project_id=")[-1].split("&")[0]
    elif body.get("project_id"):
        project_id = body["project_id"]

    response_data: Dict[str, Any] = {}

    if method == "POST" and "/api/investigate" in path:
        response_data = api_instance.trigger_investigation(project_id)
    elif method == "POST" and "/api/human-correction" in path:
        response_data = api_instance.submit_human_correction(
            project_id=project_id,
            investigation_id=body.get("investigation_id", "inv_manual_001"),
            claim_id=body.get("claim_id"),
            corrected_interpretation=body.get("corrected_interpretation", "The missing section was underground/backfilled and therefore was not visible during inspection."),
            reason_for_correction=body.get("reason_for_correction", "Underground/backfilled infrastructure may not remain visually observable after completion."),
            evidence_ids=body.get("evidence_ids", ["e1-mb", "e2-photo"]),
            corrected_by=body.get("corrected_by", "auditor_human_01")
        )
    elif "/api/project" in path:
        response_data = api_instance.get_public_project(project_id)
    elif "/api/money-trail" in path:
        response_data = api_instance.get_money_trail(project_id)
    elif "/api/evidence-graph" in path:
        response_data = api_instance.get_evidence_graph(project_id)
    elif "/api/investigation-status" in path or "/api/explanation" in path:
        response_data = api_instance.get_investigation_status(project_id)
    else:
        response_data = {"error": f"Invalid API endpoint: {path}"}

    response_bytes = json.dumps(response_data).encode("utf-8")
    status = "200 OK"
    headers = [
        ("Content-Type", "application/json"),
        ("Content-Length", str(len(response_bytes))),
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Headers", "Content-Type"),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    ]

    start_response(status, headers)
    return [response_bytes]
