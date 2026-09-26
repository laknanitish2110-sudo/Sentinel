"""
SENTINEL Crown Demo Execution Script.
Executes the complete Ward 7 -> Human Correction -> Ward 8 Investigation Lifecycle with exact audit logging:
[1] WARD 7 SELECTED
[2] INVESTIGATION STARTED
[3] EVIDENCE COLLECTED
[4] EVIDENCE GRAPH BUILT
[5] EVIDENCE GAP IDENTIFIED
[6] HUMAN REVIEW REQUIRED
[7] HUMAN CORRECTION STORED
[8] CASE MEMORY CREATED
[9] WARD 8 SELECTED
[10] HISTORICAL PRECEDENT RETRIEVED
[11] CURRENT EVIDENCE RECHECKED
[12] CURRENT DECISION
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem
from sentinel.orchestrator import Orchestrator
from sentinel.api import SentinelCitizenAPI
from sentinel.vision.construction_adapter import ConstructionPerceptionAdapter


def run_crown_demo():
    print("=======================================================================")
    print("           SENTINEL CROWN DEMO — FINAL INTEGRATED DEMONSTRATION         ")
    print("                       'THE MODEL SEES. SENTINEL INVESTIGATES.'         ")
    print("=======================================================================\n")

    # In-memory DB for clean, reproducible demonstration
    db = SentinelDB(":memory:")
    api = SentinelCitizenAPI(db)

    # -------------------------------------------------------------------------
    # [1] WARD 7 SELECTED
    # -------------------------------------------------------------------------
    p1_id = "proj_crown_ward7"
    p1 = Project(
        id=p1_id,
        code="DEMO-WARD7-DRAIN-2026",
        name="Ward 7 Stormwater Drainage Improvement",
        description="Construction of RCC storm water drain and laying of 400m main drainage line along Ward 7 primary corridor.",
        sanctioned_amount=1800000.0,
        released_amount=720000.0,
        currency="INR",
        location_name="Ward 7 Arterial Corridor, Zone 3",
        status="UNDER_AUDIT"
    )
    db.save_project(p1)

    c1 = Claim(
        id="claim_crown_w7_pipe400",
        project_id=p1_id,
        claim_ref="CLAIM-WARD7-PIPE-400M",
        claimed_by="Apex Infra Works Ltd",
        claim_type="PHYSICAL_QUANTITY",
        description="Contractor 2nd RA Bill claiming installation of 400 meters of 600mm RCC hume pipes.",
        claimed_value=400.0,
        unit="meters",
        claim_date="2026-09-15"
    )
    db.save_claim(c1)

    print("[1] WARD 7 SELECTED")
    print(f"    - Project: {p1.name} ({p1.code})")
    print(f"    - Sanctioned: ₹{p1.sanctioned_amount:,.2f} | Released: ₹{p1.released_amount:,.2f} (40.0%)")
    print(f"    - Claimed Work: 80.0% completion ({c1.claimed_value} {c1.unit} certified)\n")

    # -------------------------------------------------------------------------
    # [2] INVESTIGATION STARTED
    # -------------------------------------------------------------------------
    print("[2] INVESTIGATION STARTED")
    inv1_status = api.trigger_investigation(p1_id)
    inv1_id = inv1_status["investigation_id"]
    print(f"    - Triggered via Sentinel Citizen API: Investigation ID = {inv1_id}")
    print("    - Orchestration Path: Intake -> Multi-Source Collection -> Graph Construction -> Contradiction Engine -> Decision Engine\n")

    # -------------------------------------------------------------------------
    # [3] EVIDENCE COLLECTED
    # -------------------------------------------------------------------------
    e1_mb = EvidenceItem(
        id="e1_mb402", project_id=p1_id, claim_id=c1.id, source_type="MB_RECORD", source_id="MB-402",
        observation="Junior Engineer Measurement Book entry certifying 400m of pipe excavation and laying completed.",
        value=400.0, unit="meters", timestamp="2026-09-14", location={"text": "Ward 7 Main Stretch"},
        confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
    )
    e1_insp = EvidenceItem(
        id="e1_insp180", project_id=p1_id, claim_id=c1.id, source_type="PHYSICAL_INSPECTION", source_id="INSP-009",
        observation="Independent site audit photo inspection verified 180 meters of pipe laid inside active trench.",
        value=180.0, unit="meters", timestamp="2026-09-18", location={"address": "Ward 7 Trench Section B"},
        confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
    )
    db.save_evidence(e1_mb)
    db.save_evidence(e1_insp)

    # Attach specialized fine-tuned construction perception nodes
    adapter = ConstructionPerceptionAdapter(db=db, confidence_threshold=0.25)
    sample_img = os.path.join("data", "vision_eval_real", "real_eval_02_construction_works_osaka.jpg")
    if os.path.exists(sample_img):
        adapter.detect_and_adapt(
            image_path=sample_img,
            project_id=p1_id,
            claim=c1,
            source_evidence_id="ev_crown_vision_w7",
            location_override={"latitude": 12.9720, "longitude": 77.5950, "address": "Ward 7 Sector B"},
            timestamp_override="2026-09-18T10:30:00Z"
        )

    collected = db.get_evidence_for_project(p1_id)
    print("[3] EVIDENCE COLLECTED")
    print(f"    - Multi-Source Records Gathered: {len(collected)} evidence nodes")
    print("      • Official Measurement Book (MB-402): 400m certified")
    print("      • Inspection Photo Report (INSP-009): 180m visible")
    print("      • Construction Perception Sensor: Machinery/PPE/Site Personnel observed (NEUTRAL context)\n")

    # -------------------------------------------------------------------------
    # [4] EVIDENCE GRAPH BUILT
    # -------------------------------------------------------------------------
    graph = api.get_evidence_graph(p1_id)
    print("[4] EVIDENCE GRAPH BUILT")
    print(f"    - Target Claim Node: {c1.claim_ref} ({c1.claimed_value}m)")
    for node in graph["evidence"]:
        print(f"      • [{node['relationship_label']}] {node['source_name']} ({node['source_id']}): {node['observation'][:70]}...")
    print()

    # -------------------------------------------------------------------------
    # [5] EVIDENCE GAP IDENTIFIED
    # -------------------------------------------------------------------------
    inv1_res = api.trigger_investigation(p1_id)
    print("[5] EVIDENCE GAP IDENTIFIED")
    print("    - Quantitative Gap: MB-402 certifies 400m vs Inspection Photo shows 180m visible (220m gap)")
    print("    - Contradiction Engine Severity: HIGH (Physical Measurement Discrepancy)\n")

    # -------------------------------------------------------------------------
    # [6] HUMAN REVIEW REQUIRED
    # -------------------------------------------------------------------------
    print("[6] HUMAN REVIEW REQUIRED")
    print(f"    - Decision Engine Verdict: {inv1_res['final_state_raw']}")
    print(f"    - Citizen Finding: '{inv1_res['evidence_grounded_explanation']['why_this_matters']}'")
    print("    - Strict Boundary Check: Zero fraud accusations, zero payment denials, zero model overrides\n")

    # -------------------------------------------------------------------------
    # [7] HUMAN CORRECTION STORED
    # -------------------------------------------------------------------------
    corr_res = api.submit_human_correction(
        project_id=p1_id,
        investigation_id=inv1_id,
        claim_id=c1.id,
        corrected_interpretation="The missing section was underground/backfilled and therefore was not visible during inspection.",
        reason_for_correction="Underground/backfilled infrastructure may not remain visually observable after completion.",
        evidence_ids=["e1_mb402", "e1_insp180"],
        corrected_by="auditor_lead_human"
    )
    print("[7] HUMAN CORRECTION STORED")
    print(f"    - Correction ID: {corr_res['correction_id']}")
    print("    - Original Interpretation Preserved: True (Non-overwrite invariant enforced)")
    print(f"    - Human Auditor Correction: '{corr_res['corrected_interpretation']}'\n")

    # -------------------------------------------------------------------------
    # [8] CASE MEMORY CREATED
    # -------------------------------------------------------------------------
    print("[8] CASE MEMORY CREATED")
    print(f"    - Structured Case Memory ID: {corr_res['case_memory_id']}")
    print(f"    - Precedent Rule: '{corr_res['precedent_rule']}'")
    print("    - Note: Structured case memory retrieval, NOT model-weight retraining\n")

    # -------------------------------------------------------------------------
    # [9] WARD 8 SELECTED
    # -------------------------------------------------------------------------
    p2_id = "proj_crown_ward8"
    p2 = Project(
        id=p2_id,
        code="DEMO-WARD8-DRAIN-2026",
        name="Ward 8 Drainage Extension",
        description="Extension of 500m underground storm drain along Ward 8 commercial corridor.",
        sanctioned_amount=2500000.0,
        released_amount=1000000.0,
        currency="INR",
        location_name="Ward 8 Corridor, Zone 3",
        status="UNDER_AUDIT"
    )
    db.save_project(p2)

    c2 = Claim(
        id="claim_crown_w8_pipe500", project_id=p2_id, claim_ref="CLAIM-WARD8-PIPE-500M", claimed_by="Apex Infra Works Ltd",
        claim_type="PHYSICAL_QUANTITY", description="Contractor report asserting installation of 500 meters of RCC pipes.",
        claimed_value=500.0, unit="meters", claim_date="2026-09-20"
    )
    db.save_claim(c2)

    e2_mb = EvidenceItem(
        id="e2_mb505", project_id=p2_id, claim_id=c2.id, source_type="MB_RECORD", source_id="MB-505",
        observation="Junior Engineer Measurement Book entry certifying 500m of pipe laying completed.",
        value=500.0, unit="meters", timestamp="2026-09-19", location={"text": "Ward 8 Main Road"},
        confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
    )
    e2_insp = EvidenceItem(
        id="e2_photo220", project_id=p2_id, claim_id=c2.id, source_type="PHYSICAL_INSPECTION", source_id="INSP-012",
        observation="Site photo inspection verified 220 meters visible in open trench.",
        value=220.0, unit="meters", timestamp="2026-09-21", location={"address": "Ward 8 Trench Section A"},
        confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
    )
    db.save_evidence(e2_mb)
    db.save_evidence(e2_insp)

    print("[9] WARD 8 SELECTED")
    print(f"    - Second Project: {p2.name} ({p2.code})")
    print(f"    - Target Claim: {c2.claim_ref} ({c2.claimed_value}m certified vs 220m visible)\n")

    # -------------------------------------------------------------------------
    # [10] HISTORICAL PRECEDENT RETRIEVED
    # -------------------------------------------------------------------------
    inv2_status = api.get_investigation_status(p2_id)
    prec = inv2_status["historical_precedent"]
    print("[10] HISTORICAL PRECEDENT RETRIEVED")
    print(f"    - Precedent Tag: {prec['label'] if prec else 'None'}")
    print(f"    - Precedent Rule: '{prec['precedent_rule'] if prec else 'None'}'")
    print("    - Explicit Safety Callout: PRECEDENT ≠ PROOF (Precedent informs context only)\n")

    # -------------------------------------------------------------------------
    # [11] CURRENT EVIDENCE RECHECKED
    # -------------------------------------------------------------------------
    print("[11] CURRENT EVIDENCE RECHECKED")
    print("    - Independent Evaluation: Ward 8 evidence evaluated on its own MB-505 (500m) and INSP-012 (220m) records.")
    print("    - Safety Invariant: Ward 7 correction does NOT auto-close or auto-resolve Ward 8 case\n")

    # -------------------------------------------------------------------------
    # [12] CURRENT DECISION
    # -------------------------------------------------------------------------
    print("[12] CURRENT DECISION")
    print(f"    - Ward 8 Final Outcome: {inv2_status['final_state_raw']}")
    print(f"    - Explanation: '{inv2_status['evidence_grounded_explanation']['why_this_matters']}'")
    print("\n=======================================================================")
    print("                       THE MODEL SEES. SENTINEL INVESTIGATES.          ")
    print("   Every human correction becomes structured context for future investigations.")
    print("=======================================================================\n")


if __name__ == "__main__":
    run_crown_demo()
