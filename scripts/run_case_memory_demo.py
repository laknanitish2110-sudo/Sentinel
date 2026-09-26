"""
SENTINEL Phase 3D Demo — Human Correction to Case Memory Loop.

Demonstrates:
1. CASE A: Human auditor corrects an investigation interpretation (underground covered work).
2. Store correction & append-only case memory record.
3. CASE B: Similar evidence pattern triggers retrieval of CASE A precedent as HISTORICAL_PRECEDENT.
4. Proves current investigation is NOT auto-closed by precedent and requires current evidence.
5. Displays citizen-safe public representation stripping private auditor credentials.
"""
import os
import sys

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem
from sentinel.engines.case_memory_engine import CaseMemoryEngine
from sentinel.orchestrator import Orchestrator


def main():
    print("===============================================================")
    print(" SENTINEL PHASE 3D — HUMAN CORRECTION TO CASE MEMORY LOOP DEMO")
    print("===============================================================\n")

    db = SentinelDB()
    memory_engine = CaseMemoryEngine(db=db)

    # -------------------------------------------------------------------------
    # 1. SETUP CASE A
    # -------------------------------------------------------------------------
    print("[1] Setting up CASE A: Initial Investigation with Underground Work Discrepancy...")
    proj_a = Project(
        id="proj_case_a",
        code="PRJ-A-2026",
        name="Ward 4 Drainage Construction",
        description="Drainage project",
        sanctioned_amount=2000000.0,
        released_amount=1000000.0
    )
    db.save_project(proj_a)

    claim_a = Claim(
        id="clm_case_a",
        project_id=proj_a.id,
        claim_ref="CLM-A-01",
        claimed_by="Contractor A",
        claim_type="PHYSICAL_QUANTITY",
        description="Installed 400m RCC pipeline",
        claimed_value=400.0,
        unit="meters",
        claim_date="2026-09-10"
    )
    db.save_claim(claim_a)

    ev_photo_a = EvidenceItem(
        id="ev_photo_a",
        project_id=proj_a.id,
        claim_id=claim_a.id,
        source_type="GEO_PHOTO",
        source_id="CAM-A-01",
        observation="Surface inspection photo shows 180 meters of visible laid pipe in trench.",
        value=180.0,
        unit="meters",
        timestamp="2026-09-12T09:00:00Z",
        location={"latitude": 12.971, "longitude": 77.594},
        confidence=0.90,
        reliability="HIGH",
        relationship="NEUTRAL"
    )
    db.save_evidence(ev_photo_a)

    ev_mb_a = EvidenceItem(
        id="ev_mb_a",
        project_id=proj_a.id,
        claim_id=claim_a.id,
        source_type="MB_RECORD",
        source_id="MB-A-401",
        observation="Measurement book entry certifying 400 meters completed.",
        value=400.0,
        unit="meters",
        timestamp="2026-09-14T10:00:00Z",
        location={"latitude": 12.971, "longitude": 77.594},
        confidence=1.0,
        reliability="HIGH",
        relationship="SUPPORTS"
    )
    db.save_evidence(ev_mb_a)

    orchestrator = Orchestrator(db=db)
    res_a = orchestrator.run_investigation(proj_a.id, claim_a.id)
    print(f"CASE A Initial Investigation State: {res_a['final_state']}")
    print(f"CASE A Initial Decision Notes:       {res_a['decision_notes']}")

    # -------------------------------------------------------------------------
    # 2. AUDITOR HUMAN CORRECTION FOR CASE A
    # -------------------------------------------------------------------------
    print("\n[2] Applying Auditor Human Correction for CASE A...")
    original_interp = "Surface photo shows only 180m visible, conflicting with 400m MB claim."
    corrected_interp = "400m pipeline is physically installed; remaining 220m section was backfilled and underground."
    human_reason = "Underground excavation logs and soil backfill evidence confirm pipeline was laid and covered prior to surface photograph."
    auditor_id = "AUDITOR-SYS-4099"

    correction, memory = memory_engine.process_human_correction(
        investigation_id=res_a["investigation_id"],
        project_id=proj_a.id,
        claim_id=claim_a.id,
        corrected_by=auditor_id,
        original_interpretation=original_interp,
        corrected_interpretation=corrected_interp,
        reason_for_correction=human_reason,
        evidence_ids_involved=[ev_photo_a.id, ev_mb_a.id],
        pattern_type="UNDERGROUND_COVERED_WORK",
        user_role="auditor"
    )

    print(f"Human Correction Saved: ID={correction.id}")
    print(f"  Original Interp:  {correction.original_interpretation}")
    print(f"  Corrected Interp: {correction.corrected_interpretation}")
    print(f"  Auditor Reason:   {correction.reason_for_correction}")
    print(f"Case Memory Record Saved: ID={memory.id}, Pattern={memory.pattern_type}")

    # -------------------------------------------------------------------------
    # 3. SETUP CASE B & RETRIEVE PRECEDENT
    # -------------------------------------------------------------------------
    print("\n[3] Setting up CASE B with Similar Evidence Pattern...")
    proj_b = Project(
        id="proj_case_b",
        code="PRJ-B-2026",
        name="Ward 9 Stormwater Drain Project",
        description="New drainage project",
        sanctioned_amount=3000000.0,
        released_amount=1500000.0
    )
    db.save_project(proj_b)

    claim_b = Claim(
        id="clm_case_b",
        project_id=proj_b.id,
        claim_ref="CLM-B-01",
        claimed_by="Contractor B",
        claim_type="PHYSICAL_QUANTITY",
        description="Installed 350m RCC pipeline",
        claimed_value=350.0,
        unit="meters",
        claim_date="2026-09-20"
    )
    db.save_claim(claim_b)

    ev_photo_b = EvidenceItem(
        id="ev_photo_b",
        project_id=proj_b.id,
        claim_id=claim_b.id,
        source_type="GEO_PHOTO",
        source_id="CAM-B-01",
        observation="Surface inspection photo shows 150 meters of visible laid pipe in trench.",
        value=150.0,
        unit="meters",
        timestamp="2026-09-21T09:00:00Z",
        location={"latitude": 12.980, "longitude": 77.600},
        confidence=0.91,
        reliability="HIGH",
        relationship="NEUTRAL"
    )
    db.save_evidence(ev_photo_b)

    ev_mb_b = EvidenceItem(
        id="ev_mb_b",
        project_id=proj_b.id,
        claim_id=claim_b.id,
        source_type="MB_RECORD",
        source_id="MB-B-102",
        observation="Measurement book entry certifying 350 meters completed.",
        value=350.0,
        unit="meters",
        timestamp="2026-09-22T10:00:00Z",
        location={"latitude": 12.980, "longitude": 77.600},
        confidence=1.0,
        reliability="HIGH",
        relationship="SUPPORTS"
    )
    db.save_evidence(ev_mb_b)

    print("\n[4] Querying Historical Case Memory for CASE B Pattern...")
    precedents = memory_engine.find_similar_precedents("UNDERGROUND_COVERED_WORK")
    print(f"Retrieved {len(precedents)} Historical Precedent(s):")
    for p in precedents:
        print(f"  Precedent Pattern:  {p['pattern_type']}")
        print(f"  Precedent Rule:     {p['precedent_rule']}")
        print(f"  Original Interp:    {p['original_interpretation']}")
        print(f"  Corrected Interp:   {p['corrected_interpretation']}")

    # -------------------------------------------------------------------------
    # 4. RUN CASE B INVESTIGATION WITH HISTORICAL PRECEDENT
    # -------------------------------------------------------------------------
    print("\n[5] Executing CASE B Investigation with Surfaced Precedent...")
    res_b = orchestrator.run_investigation(proj_b.id, claim_b.id)

    print(f"CASE B Investigation Final State: {res_b['final_state']}")
    print(f"CASE B Decision Notes:            {res_b['decision_notes']}")

    # 5. Verify Invariant: Current investigation is NOT auto-closed
    if res_b["final_state"] == "CLOSED":
        print("\n[FAILURE] Invariant violated: Precedent auto-closed current case!")
        sys.exit(1)
    else:
        print(f"\n[SUCCESS] Invariant verified: CASE B state is '{res_b['final_state']}'. Precedent surfaced without auto-closing!")

    # -------------------------------------------------------------------------
    # 5. CITIZEN API REPRESENTATION
    # -------------------------------------------------------------------------
    print("\n[6] Formatting Citizen-Safe Representation...")
    citizen_summary = memory_engine.get_citizen_case_memory_summary("UNDERGROUND_COVERED_WORK")
    print("\n--- PUBLIC CITIZEN CASE MEMORY RESPONSE ---")
    for c_rec in citizen_summary:
        print(f"Notice:       {c_rec['public_notice']}")
        print(f"Category:     {c_rec['pattern_category']}")
        print(f"Original:     {c_rec['original_interpretation']}")
        print(f"Auditor Fix:  {c_rec['auditor_corrected_interpretation']}")
        print(f"Reason:       {c_rec['correction_reason']}")

    # Verify auditor privacy
    raw_str = str(citizen_summary)
    if auditor_id in raw_str:
        print(f"\n[FAILURE] Privacy leak: Auditor ID '{auditor_id}' exposed in citizen API!")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Privacy verified: Auditor identifier stripped from public citizen response.")

    print("\n===============================================================")
    print(" DEMO COMPLETE — CASE MEMORY LOOP VERIFIED SUCCESSFULLY")
    print("===============================================================")


if __name__ == "__main__":
    main()
