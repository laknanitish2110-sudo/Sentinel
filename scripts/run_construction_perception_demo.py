"""
Phase 4C Construction Perception Demo Script.
Demonstrates end-to-end integration:
Real Image -> ConstructionPerceptionAdapter -> EvidenceContract -> EvidenceGraph -> ContradictionEngine -> DecisionEngine.
"""
import os
from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem
from sentinel.vision.construction_adapter import ConstructionPerceptionAdapter
from sentinel.engines.contradiction_engine import ContradictionEngine
from sentinel.engines.decision_engine import DecisionEngine

def run_demo():
    db = SentinelDB()
    adapter = ConstructionPerceptionAdapter(db=db, confidence_threshold=0.25)
    contradiction_engine = ContradictionEngine(db=db)
    decision_engine = DecisionEngine()

    project_id = "proj_ward7_drainage"
    
    # Save project first to satisfy SQLite foreign key constraints
    project = Project(
        id=project_id,
        code="WARD7-DRAIN-2026",
        name="Ward 7 Stormwater Drainage Construction",
        description="Construction of 400m RCC box culvert and underground drainage network",
        sanctioned_amount=5000000.0,
        released_amount=2500000.0,
        currency="INR",
        location_name="Ward 7 Sector B"
    )
    db.save_project(project)

    claim = Claim(
        id="claim_ward7_drain_001",
        project_id=project_id,
        claim_ref="CLAIM-2026-001",
        claimed_by="Contractor Corp",
        claim_type="PROGRESS_PAYMENT",
        description="Certified 400 meters of concrete drainage trench excavation and pipe laying.",
        claimed_value=400.0,
        unit="meters",
        claim_date="2026-09-15T08:00:00Z"
    )
    db.save_claim(claim)

    sample_image = os.path.join("data", "vision_eval_real", "real_eval_02_construction_works_osaka.jpg")

    print("=== Step 1: Ingest Real Image via ConstructionPerceptionAdapter ===")
    evidence_nodes = adapter.detect_and_adapt(
        image_path=sample_image,
        project_id=project_id,
        claim=claim,
        source_evidence_id="evi_osaka_real_001",
        location_override={"latitude": 12.9720, "longitude": 77.5950, "address": "Ward 7 Sector B"},
        timestamp_override="2026-09-18T10:30:00Z"
    )
    print(f"Generated {len(evidence_nodes)} EvidenceItem nodes for Evidence Graph:")
    for node in evidence_nodes:
        print(f"  - ID: {node.id} | Class: {node.metadata['detected_class']} | Primitive: {node.metadata['visual_primitive']} | Conf: {node.confidence:.4f} | Rel: {node.relationship}")

    print("\n=== Step 2: Query All Evidence for Project from Evidence Graph ===")
    all_evidence = db.get_evidence_for_project(project_id)
    print(f"Total Evidence Nodes in DB for project '{project_id}': {len(all_evidence)}")

    print("\n=== Step 3: Run ContradictionEngine over Evidence Graph ===")
    contradictions = contradiction_engine.evaluate_contradictions(
        investigation_id="inv_demo_4c_001",
        project_id=project_id,
        claim_id=claim.id,
        evidence_items=all_evidence
    )
    print(f"Contradictions detected: {len(contradictions)}")
    for c in contradictions:
        print(f"  - Contradiction ID: {c.id} | Severity: {c.severity} | Description: {c.conflict_description}")

    print("\n=== Step 4: Run DecisionEngine for Authoritative Investigation Judgment ===")
    state, notes = decision_engine.evaluate_decision(
        agent_results=[],
        contradictions=contradictions,
        evidence_items=all_evidence,
        case_memories=[]
    )
    print(f"Decision State: {state.value}")
    print(f"Decision Notes: {notes}")

if __name__ == "__main__":
    run_demo()
