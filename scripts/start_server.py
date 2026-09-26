"""
SENTINEL HTTP Web & API Server Script.
Serves the citizen-facing web application and API endpoints on http://localhost:8000.
"""
import sys
import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem, HumanCorrection, CaseMemoryRecord
from sentinel.api import SentinelCitizenAPI

# Global DB and API instances
db_instance: Optional[SentinelDB] = None
api_instance: Optional[SentinelCitizenAPI] = None

DEMO_PROJECT_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


def init_demo_db():
    global db_instance, api_instance
    db_instance = SentinelDB(":memory:")
    
    # 1. Project
    p = Project(
        id=DEMO_PROJECT_ID,
        code="DEMO-WARD7-DRAIN-2026",
        name="Ward 7 Drainage Improvement [DEMO DATA]",
        description="Construction of RCC storm water drain and laying of 400m main drainage line along Ward 7 primary arterial road.",
        sanctioned_amount=1800000.0,
        released_amount=720000.0,
        currency="INR",
        location_name="Ward 7 Arterial Corridor, Zone 3",
        status="UNDER_AUDIT",
        metadata={"is_demo_data": True}
    )
    db_instance.save_project(p)

    # 2. Claims
    c1 = Claim(
        id="c1-ra2", project_id=p.id, claim_ref="CLAIM-WARD7-RA-02", claimed_by="Apex Infra Works Ltd",
        claim_type="COMPLETION_PERCENTAGE", description="Contractor submission for 2nd RA Bill claiming 80% completion.",
        claimed_value=80.0, unit="percent", claim_date="2026-09-15"
    )
    c2 = Claim(
        id="c2-pipe400", project_id=p.id, claim_ref="CLAIM-WARD7-PIPE-400M", claimed_by="Apex Infra Works Ltd",
        claim_type="PHYSICAL_QUANTITY", description="Contractor report asserting full installation of 400 meters of 600mm RCC hume pipes.",
        claimed_value=400.0, unit="meters", claim_date="2026-09-15"
    )
    db_instance.save_claim(c1)
    db_instance.save_claim(c2)

    # 3. Evidence
    e1 = EvidenceItem(
        id="e1-mb", project_id=p.id, claim_id=c2.id, source_type="MB_RECORD", source_id="MB-BOOK-402/PAGE-18",
        observation="Junior Engineer Measurement Book entry certifying 400m of pipe excavation and laying completed.",
        value=400.0, unit="meters", timestamp="2026-09-14", location={"text": "Ward 7 Main Stretch"},
        confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
    )
    e2 = EvidenceItem(
        id="e2-photo", project_id=p.id, claim_id=c2.id, source_type="PHYSICAL_INSPECTION", source_id="INSP-2026-W7-009",
        observation="Independent site audit photo inspection verified only 180 meters of pipe laid inside active trench.",
        value=180.0, unit="meters", timestamp="2026-09-18", location={"address": "Ward 7 Trench Section B"},
        confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
    )
    e3 = EvidenceItem(
        id="e3-inv", project_id=p.id, claim_id=c2.id, source_type="INVOICE", source_id="INV-SOUTHERN-CONCRETE-9941",
        observation="Invoice from Southern Concrete Products confirming procurement and delivery of 400m of RCC hume pipes to site.",
        value=400.0, unit="meters", timestamp="2026-09-02", location={"delivery": "Ward 7 Staging Yard"},
        confidence=0.98, reliability="HIGH", relationship="NEUTRAL", metadata={"invoice_amount": 480000.0}
    )
    e4 = EvidenceItem(
        id="e4-bank", project_id=p.id, claim_id=c1.id, source_type="BANK_STATEMENT", source_id="TREASURY-DISBURSEMENT-MISSING-02",
        observation="Treasury records confirm Tranche 1 release (₹7,20,000), but official Bank Clearance Certificate for second claimed tranche is unverified/absent.",
        value=720000.0, unit="INR", timestamp="2026-08-10", location=None,
        confidence=0.50, reliability="UNVERIFIED", relationship="INSUFFICIENT"
    )
    db_instance.save_evidence(e1)
    db_instance.save_evidence(e2)
    db_instance.save_evidence(e3)
    db_instance.save_evidence(e4)

    api_instance = SentinelCitizenAPI(db_instance)


class SentinelRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        public_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public"))
        super().__init__(*args, directory=public_dir, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._handle_api()
        else:
            super().do_GET()

    def _handle_api(self):
        global api_instance
        if not api_instance:
            init_demo_db()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        response_data = {}
        if self.path.startswith("/api/project"):
            response_data = api_instance.get_public_project(DEMO_PROJECT_ID)
        elif self.path.startswith("/api/money-trail"):
            response_data = api_instance.get_money_trail(DEMO_PROJECT_ID)
        elif self.path.startswith("/api/evidence-graph"):
            response_data = api_instance.get_evidence_graph(DEMO_PROJECT_ID)
        elif self.path.startswith("/api/investigation-status"):
            response_data = api_instance.get_investigation_status(DEMO_PROJECT_ID)
        else:
            response_data = {"error": "Invalid API endpoint"}

        self.wfile.write(json.dumps(response_data).encode("utf-8"))


def main():
    init_demo_db()
    port = 8000
    server_address = ("", port)
    httpd = HTTPServer(server_address, SentinelRequestHandler)
    print(f"[SENTINEL] Citizen Web App & API running at http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[SENTINEL] Server stopped.")
        httpd.server_close()


if __name__ == "__main__":
    main()
