"""
Demo scenario execution script for Sentinel Phase 1A.
Demonstrates Scenarios A, B, and C.
"""
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem
from sentinel.orchestrator import Orchestrator
from sentinel.engines.case_memory_engine import CaseMemoryEngine


def run_demo():
    db = SentinelDB(":memory:")
    
    # 1. Setup Project
    p = Project(
        id="p-ward7",
        code="DEMO-WARD7-DRAIN-2026",
        name="Ward 7 Drainage Improvement [DEMO DATA]",
        description="Construction of RCC storm water drain.",
        sanctioned_amount=1800000.0,
        released_amount=720000.0
    )
    db.save_project(p)

    c = Claim(
        id="c-400m",
        project_id=p.id,
        claim_ref="CLAIM-WARD7-PIPE-400M",
        claimed_by="Apex Infra Works Ltd",
        claim_type="PHYSICAL_QUANTITY",
        description="Full installation of 400m of 600mm RCC hume pipes",
        claimed_value=400.0,
        unit="meters",
        claim_date="2026-09-15"
    )
    db.save_claim(c)

    # 2. Seed Evidence for Scenario B (Contradiction)
    ev_mb = EvidenceItem(
        id="e-mb-400", project_id=p.id, claim_id=c.id, source_type="MB_RECORD", source_id="MB-402",
        observation="JE certified 400m pipe installation completed.", value=400.0, unit="meters",
        timestamp="2026-09-14", location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
    )
    ev_photo = EvidenceItem(
        id="e-photo-180", project_id=p.id, claim_id=c.id, source_type="PHYSICAL_INSPECTION", source_id="INSP-009",
        observation="Photo inspection verified only 180m pipe laid in trench.", value=180.0, unit="meters",
        timestamp="2026-09-18", location={"address": "Ward 7 Trench Section B"}, confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
    )
    ev_inv = EvidenceItem(
        id="e-inv-400", project_id=p.id, claim_id=c.id, source_type="INVOICE", source_id="INV-9941",
        observation="Invoice confirms procurement and delivery of 400m hume pipes to site.", value=400.0, unit="meters",
        timestamp="2026-09-02", location=None, confidence=0.98, reliability="HIGH", relationship="NEUTRAL",
        metadata={"invoice_amount": 480000.0}
    )

    db.save_evidence(ev_mb)
    db.save_evidence(ev_photo)
    db.save_evidence(ev_inv)

    orchestrator = Orchestrator(db)

    print("======================================================================")
    print("SCENARIO B: INITIAL INVESTIGATION (CONTRADICTION DETECTED)")
    print("======================================================================")
    res_b = orchestrator.run_investigation(project_id=p.id, claim_id=c.id)
    print(f"Final State: {res_b['final_state']}")
    print(f"Decision Notes: {res_b['decision_notes']}")
    print(f"Contradictions Found: {res_b['contradiction_count']}")
    print("Agent Results:")
    print(json.dumps(res_b["agent_results"], indent=2))

    print("\n======================================================================")
    print("SCENARIO C: HUMAN AUDITOR CORRECTION & CASE MEMORY PERSISTENCE")
    print("======================================================================")
    cm_engine = CaseMemoryEngine(db)
    corr, mem = cm_engine.process_human_correction(
        investigation_id=res_b["investigation_id"],
        project_id=p.id,
        claim_id=c.id,
        corrected_by="Chief Municipal Auditor K. Sharma",
        original_interpretation="Flagged 220m as unexecuted work based solely on trench photo.",
        corrected_interpretation="180m laid in trench, plus 220m stacked in contractor site yard ready for laying.",
        reason_for_correction="Trench photo omits contractor staging yard where remaining 220m of Hume pipes were stacked.",
        evidence_ids_involved=[ev_mb.id, ev_photo.id, ev_inv.id],
        pattern_type="STAGED_MATERIAL_DISCREPANCY",
        user_role="auditor"
    )
    print(f"Human Correction Saved: ID {corr.id} by {corr.corrected_by}")
    print(f"Case Memory Created: Pattern [{mem.pattern_type}]")
    print(f"Precedent Rule: {mem.precedent_rule}")

    print("\n======================================================================")
    print("SCENARIO C (FOLLOW-UP): SUBSEQUENT INVESTIGATION INHERITS PRECEDENT")
    print("======================================================================")
    res_c = orchestrator.run_investigation(project_id=p.id, claim_id=c.id)
    print(f"Final State: {res_c['final_state']}")
    print(f"Decision Notes: {res_c['decision_notes']}")

    db.close()


if __name__ == "__main__":
    run_demo()
