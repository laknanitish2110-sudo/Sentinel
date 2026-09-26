"""
SENTINEL Phase 2B & 2B.1 Automated Test Suite.
Covers Vision Simulator, Vision Evidence Adapter (Perception-Only Boundary Correction), DB persistence, Contradiction Engine flow, and Citizen API graph rendering.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem, InvestigationState
from sentinel.vision import MockVisionSimulator, VisionEvidenceAdapter
from sentinel.engines.contradiction_engine import ContradictionEngine
from sentinel.orchestrator import Orchestrator
from sentinel.api import SentinelCitizenAPI


class TestSentinelPhase2B(unittest.TestCase):

    def setUp(self):
        self.db = SentinelDB(":memory:")
        self.project_id = "p-vision-2b"
        self.project = Project(
            id=self.project_id,
            code="DEMO-VISION-2026",
            name="Ward 7 Vision Drainage Project [DEMO DATA]",
            description="Drainage project verified via computer vision.",
            sanctioned_amount=1800000.0,
            released_amount=720000.0
        )
        self.db.save_project(self.project)

        self.claim = Claim(
            id="c-vision-400m",
            project_id=self.project_id,
            claim_ref="CLAIM-PIPE-400M",
            claimed_by="Apex Infra Works Ltd",
            claim_type="PHYSICAL_QUANTITY",
            description="Full installation of 400m of 600mm RCC hume pipes",
            claimed_value=400.0,
            unit="meters",
            claim_date="2026-09-15"
        )
        self.db.save_claim(self.claim)

        self.simulator = MockVisionSimulator()
        self.adapter = VisionEvidenceAdapter(self.db)

    def tearDown(self):
        self.db.close()

    # -------------------------------------------------------------------------
    # Test 1: Vision Simulator Output Test
    # -------------------------------------------------------------------------
    def test_1_vision_simulator_output(self):
        raw_vision = self.simulator.analyze_site_photo(
            image_uri="storage://site-photos/ward7_trench_section_b.jpg",
            detected_length_meters=180.0,
            staged_pipe_count=22
        )
        self.assertEqual(raw_vision["primary_detected_value"], 180.0)
        self.assertEqual(raw_vision["vision_model"], "mock-yolov8-drainage-v1")
        self.assertEqual(len(raw_vision["bounding_boxes"]), 2)
        self.assertIn("180.0 meters", raw_vision["observation"])

    # -------------------------------------------------------------------------
    # Test 2: Phase 2B.1 Perception-Only Boundary Test (Never Auto-Contradicts)
    # -------------------------------------------------------------------------
    def test_2_vision_adapter_perception_only_neutral(self):
        raw_vision = self.simulator.analyze_site_photo("storage://photo.jpg", detected_length_meters=180.0)
        ev_item = self.adapter.adapt_vision_payload(self.project_id, self.claim, raw_vision)

        self.assertIsNotNone(ev_item.id)
        self.assertEqual(ev_item.project_id, self.project_id)
        self.assertEqual(ev_item.claim_id, self.claim.id)
        self.assertEqual(ev_item.source_type, "GEO_PHOTO")
        self.assertEqual(ev_item.value, 180.0)
        self.assertEqual(ev_item.unit, "meters")
        # Perception-Only Correction: Raw vision MUST default to NEUTRAL, never CONTRADICTS
        self.assertEqual(ev_item.relationship, "NEUTRAL")

    # -------------------------------------------------------------------------
    # Test 3: Bounding Box & EXIF Metadata Preservation Test
    # -------------------------------------------------------------------------
    def test_3_metadata_preservation(self):
        raw_vision = self.simulator.analyze_site_photo("storage://photo.jpg", detected_length_meters=180.0)
        ev_item = self.adapter.adapt_vision_payload(self.project_id, self.claim, raw_vision)

        meta = ev_item.metadata
        self.assertIn("bounding_boxes", meta)
        self.assertEqual(len(meta["bounding_boxes"]), 2)
        self.assertIn("exif", meta)
        self.assertEqual(meta["exif"]["camera"], "iPhone 14 Pro")
        self.assertEqual(meta["vision_model"], "mock-yolov8-drainage-v1")

    # -------------------------------------------------------------------------
    # Test 4: Vision Evidence Database Ingestion Test
    # -------------------------------------------------------------------------
    def test_4_vision_db_ingestion(self):
        raw_vision = self.simulator.analyze_site_photo("storage://photo.jpg", detected_length_meters=180.0)
        ev_item = self.adapter.adapt_vision_payload(self.project_id, self.claim, raw_vision)

        retrieved_ev = self.db.get_evidence_for_project(self.project_id)
        self.assertEqual(len(retrieved_ev), 1)
        self.assertEqual(retrieved_ev[0].id, ev_item.id)
        self.assertEqual(retrieved_ev[0].relationship, "NEUTRAL")
        self.assertEqual(retrieved_ev[0].metadata["vision_model"], "mock-yolov8-drainage-v1")

    # -------------------------------------------------------------------------
    # Test 5: Contradiction Engine Identifies 180m vs 400m Conflict
    # -------------------------------------------------------------------------
    def test_5_contradiction_engine_identifies_conflict(self):
        # 1. Official MB evidence (400m)
        ev_mb = EvidenceItem(
            id="e-mb-400", project_id=self.project_id, claim_id=self.claim.id, source_type="MB_RECORD",
            source_id="MB-402", observation="JE certified 400m pipe installation completed.", value=400.0,
            unit="meters", timestamp="2026-09-14", location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        self.db.save_evidence(ev_mb)

        # 2. Perception-Only Vision photo evidence (180m observed, ingested as NEUTRAL)
        raw_vision = self.simulator.analyze_site_photo("storage://trench_photo.jpg", detected_length_meters=180.0)
        ev_vision = self.adapter.adapt_vision_payload(self.project_id, self.claim, raw_vision)
        self.assertEqual(ev_vision.relationship, "NEUTRAL")

        # Contradiction Engine compares values and flags discrepancy
        all_ev = self.db.get_evidence_for_project(self.project_id)
        con_engine = ContradictionEngine(self.db)
        contradictions = con_engine.evaluate_contradictions("inv-v1", self.project_id, self.claim.id, all_ev)

        self.assertEqual(len(contradictions), 1)
        self.assertEqual(contradictions[0].evidence_a_id, ev_mb.id)
        self.assertEqual(contradictions[0].evidence_b_id, ev_vision.id)
        self.assertEqual(contradictions[0].severity, "HIGH")

    # -------------------------------------------------------------------------
    # Test 6: Vision Evidence Orchestration Reaches HUMAN_REVIEW_REQUIRED
    # -------------------------------------------------------------------------
    def test_6_vision_orchestration_reaches_human_review(self):
        ev_mb = EvidenceItem(
            id="e-mb-400", project_id=self.project_id, claim_id=self.claim.id, source_type="MB_RECORD",
            source_id="MB-402", observation="JE cert 400m", value=400.0, unit="meters", timestamp="2026-09-14",
            location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        self.db.save_evidence(ev_mb)

        raw_vision = self.simulator.analyze_site_photo("storage://photo.jpg", detected_length_meters=180.0)
        self.adapter.adapt_vision_payload(self.project_id, self.claim, raw_vision)

        orchestrator = Orchestrator(self.db)
        res = orchestrator.run_investigation(self.project_id, self.claim.id)

        self.assertEqual(res["final_state"], InvestigationState.HUMAN_REVIEW_REQUIRED)
        self.assertEqual(res["contradiction_count"], 1)

    # -------------------------------------------------------------------------
    # Test 7: Citizen API Evidence Graph Renders Contradiction Badge
    # -------------------------------------------------------------------------
    def test_7_vision_node_render_in_citizen_graph_api(self):
        ev_mb = EvidenceItem(
            id="e-mb-400", project_id=self.project_id, claim_id=self.claim.id, source_type="MB_RECORD",
            source_id="MB-402", observation="JE cert 400m", value=400.0, unit="meters", timestamp="2026-09-14",
            location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        self.db.save_evidence(ev_mb)

        raw_vision = self.simulator.analyze_site_photo("storage://photo.jpg", detected_length_meters=180.0)
        ev_v = self.adapter.adapt_vision_payload(self.project_id, self.claim, raw_vision)

        # Run investigation to create contradiction record
        orchestrator = Orchestrator(self.db)
        orchestrator.run_investigation(self.project_id, self.claim.id)

        api = SentinelCitizenAPI(self.db)
        graph = api.get_evidence_graph(self.project_id)

        ev_nodes = graph["evidence"]
        vision_node = next(e for e in ev_nodes if e["id"] == ev_v.id)
        self.assertEqual(vision_node["source_type"], "GEO_PHOTO")
        self.assertEqual(vision_node["relationship"], "CONTRADICTS")
        self.assertEqual(vision_node["badge_icon"], "✕")


if __name__ == "__main__":
    unittest.main()
