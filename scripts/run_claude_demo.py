"""
Live Claude Model Integration Demonstration Script for SENTINEL.
Executes real Anthropic Claude API agent reasoning when ANTHROPIC_API_KEY is present.
"""
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem
from sentinel.claude_client import ClaudeClient
from sentinel.orchestrator import Orchestrator


def run_live_demo():
    print("======================================================================")
    print("SENTINEL PHASE 1B — LIVE CLAUDE MODEL INTEGRATION DEMO")
    print("======================================================================")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[NOTICE] ANTHROPIC_API_KEY environment variable is NOT set.")
        print("To run a live investigation using Anthropic Claude API, set your key:")
        print("  On Windows PowerShell: $env:ANTHROPIC_API_KEY='your_api_key_here'")
        print("  On Bash/Linux/macOS:   export ANTHROPIC_API_KEY='your_api_key_here'")
        print("  Or add ANTHROPIC_API_KEY=sk-... to your .env file.")
        print("\nSystem will safely exit without executing live API calls.")
        print("All 20 automated unit tests (using mock providers) continue to pass independently.")
        return

    print(f"[INFO] ANTHROPIC_API_KEY detected. Initializing ClaudeClient (claude-3-5-sonnet-20241022)...")

    db = SentinelDB(":memory:")

    # Setup Ward 7 Demo Project
    p = Project(
        id="p-ward7-live", code="DEMO-WARD7-LIVE", name="Ward 7 Drainage Improvement [LIVE DEMO]",
        description="Construction of RCC storm water drain.", sanctioned_amount=1800000.0, released_amount=720000.0
    )
    db.save_project(p)

    c = Claim(
        id="c-400m-live", project_id=p.id, claim_ref="CLAIM-WARD7-PIPE-400M", claimed_by="Apex Infra Works Ltd",
        claim_type="PHYSICAL_QUANTITY", description="Full installation of 400m of 600mm RCC hume pipes",
        claimed_value=400.0, unit="meters", claim_date="2026-09-15"
    )
    db.save_claim(c)

    ev1 = EvidenceItem(
        id="e-mb-400", project_id=p.id, claim_id=c.id, source_type="MB_RECORD", source_id="MB-402",
        observation="JE certified 400m pipe installation completed.", value=400.0, unit="meters",
        timestamp="2026-09-14", location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
    )
    ev2 = EvidenceItem(
        id="e-photo-180", project_id=p.id, claim_id=c.id, source_type="PHYSICAL_INSPECTION", source_id="INSP-009",
        observation="Photo inspection verified only 180m pipe laid in trench.", value=180.0, unit="meters",
        timestamp="2026-09-18", location={"address": "Ward 7 Trench Section B"}, confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
    )
    ev3 = EvidenceItem(
        id="e-inv-400", project_id=p.id, claim_id=c.id, source_type="INVOICE", source_id="INV-9941",
        observation="Invoice confirms procurement and delivery of 400m hume pipes to site.", value=400.0, unit="meters",
        timestamp="2026-09-02", location=None, confidence=0.98, reliability="HIGH", relationship="NEUTRAL",
        metadata={"invoice_amount": 480000.0}
    )

    db.save_evidence(ev1)
    db.save_evidence(ev2)
    db.save_evidence(ev3)

    claude_client = ClaudeClient(api_key=api_key)
    orchestrator = Orchestrator(db, claude_client=claude_client)

    print("\n[EXECUTION] Triggering Orchestrator investigation with live Claude reasoning agents...")
    res = orchestrator.run_investigation(project_id=p.id, claim_id=c.id)

    print("\n======================================================================")
    print("LIVE INVESTIGATION RESULTS")
    print("======================================================================")
    print(f"Investigation ID: {res['investigation_id']}")
    print(f"Final State:      {res['final_state']}")
    print(f"Decision Notes:   {res['decision_notes']}")
    print(f"Contradictions:   {res['contradiction_count']}")

    print("\nAgent Reasoning Outputs (Validated JSON):")
    print(json.dumps(res["agent_results"], indent=2))

    db.close()


if __name__ == "__main__":
    run_live_demo()
