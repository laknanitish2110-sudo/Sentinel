"""
SENTINEL Phase 3A Automated Test Suite.
Covers real image YOLO inference integration, bounding box telemetry, Vision Adapter perception-only intake, DB ingestion, Contradiction Engine, and Citizen API graph rendering.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem, InvestigationState
from sentinel.vision import YOLODetector, VisionEvidenceAdapter
from sentinel.engines.contradiction_engine import ContradictionEngine
from sentinel.orchestrator import Orchestrator
from sentinel.api import SentinelCitizenAPI


class TestSentinelPhase3A(unittest.TestCase):

    def setUp(self):
        self.db = SentinelDB(":memory:")
        self.project_id = "p-yolo-3a"
        self.project = Project(
            id=self.project_id,
            code="DEMO-YOLO-2026",
            name="Ward 7 Real YOLO Drainage Project [DEMO DATA]",
            description="Drainage project verified via pretrained YOLO vision model.",
            sanctioned_amount=1800000.0,
            released_amount=720000.0
        )
        self.db.save_project(self.project)

        self.claim = Claim(
            id="c-yolo-400m",
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

        self.detector = YOLODetector(model_name="yolov8n-drainage.pt")
        self.adapter = VisionEvidenceAdapter(self.db)

    def tearDown(self):
        self.db.close()

    # -------------------------------------------------------------------------
    # Test 1: Real Image YOLO Inference Test
    # -------------------------------------------------------------------------
    def test_1_yolo_image_inference(self):
        raw_detection = self.detector.detect_image(
            image_path_or_uri="storage://site-photos/ward7_trench_section_b.jpg",
            target_class="installed_pipe"
        )
        self.assertEqual(raw_detection["vision_model"], "yolov8n-drainage.pt")
        self.assertEqual(raw_detection["primary_detected_value"], 180.0)
        self.assertEqual(raw_detection["unit"], "meters")
        self.assertIn("180.0 meters", raw_detection["observation"])

    # -------------------------------------------------------------------------
    # Test 2: Bounding Box & EXIF Telemetry Test
    # -------------------------------------------------------------------------
    def test_2_bounding_box_and_exif_telemetry(self):
        raw_detection = self.detector.detect_image("storage://photo.jpg")
        boxes = raw_detection["bounding_boxes"]
        self.assertGreaterEqual(len(boxes), 2)
        self.assertEqual(boxes[0]["class"], "installed_pipe")
        self.assertEqual(boxes[1]["class"], "staged_pipe_uninstalled")

        exif = raw_detection["exif"]
        self.assertEqual(exif["camera"], "iPhone 14 Pro")
        self.assertEqual(raw_detection["image_width"], 1920)
        self.assertEqual(raw_detection["image_height"], 1080)

    # -------------------------------------------------------------------------
    # Test 3: YOLO Output Connected to Perception-Only Vision Adapter Test
    # -------------------------------------------------------------------------
    def test_3_yolo_to_perception_only_adapter(self):
        raw_detection = self.detector.detect_image("storage://photo.jpg")
        ev_item = self.adapter.adapt_vision_payload(self.project_id, self.claim, raw_detection)

        self.assertIsNotNone(ev_item.id)
        self.assertEqual(ev_item.project_id, self.project_id)
        self.assertEqual(ev_item.claim_id, self.claim.id)
        self.assertEqual(ev_item.source_type, "GEO_PHOTO")
        self.assertEqual(ev_item.value, 180.0)
        self.assertEqual(ev_item.unit, "meters")
        # Perception-Only invariant: MUST enter as NEUTRAL
        self.assertEqual(ev_item.relationship, "NEUTRAL")

    # -------------------------------------------------------------------------
    # Test 4: YOLO Evidence DB Ingestion & JSONB Metadata Test
    # -------------------------------------------------------------------------
    def test_4_yolo_db_ingestion_and_jsonb_metadata(self):
        raw_detection = self.detector.detect_image("storage://photo.jpg")
        ev_item = self.adapter.adapt_vision_payload(self.project_id, self.claim, raw_detection)

        retrieved = self.db.get_evidence_for_project(self.project_id)
        self.assertEqual(len(retrieved), 1)
        meta = retrieved[0].metadata
        self.assertEqual(meta["vision_model"], "yolov8n-drainage.pt")
        self.assertEqual(len(meta["bounding_boxes"]), 2)
        self.assertEqual(meta["exif"]["camera"], "iPhone 14 Pro")

    # -------------------------------------------------------------------------
    # Test 5: YOLO Evidence Contradiction Engine Analysis Test
    # -------------------------------------------------------------------------
    def test_5_yolo_contradiction_engine_analysis(self):
        ev_mb = EvidenceItem(
            id="e-mb-400", project_id=self.project_id, claim_id=self.claim.id, source_type="MB_RECORD",
            source_id="MB-402", observation="JE cert 400m pipe installation completed.", value=400.0,
            unit="meters", timestamp="2026-09-14", location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        self.db.save_evidence(ev_mb)

        raw_detection = self.detector.detect_image("storage://photo.jpg")
        ev_yolo = self.adapter.adapt_vision_payload(self.project_id, self.claim, raw_detection)
        self.assertEqual(ev_yolo.relationship, "NEUTRAL")

        all_ev = self.db.get_evidence_for_project(self.project_id)
        con_engine = ContradictionEngine(self.db)
        contradictions = con_engine.evaluate_contradictions("inv-3a", self.project_id, self.claim.id, all_ev)

        self.assertEqual(len(contradictions), 1)
        self.assertEqual(contradictions[0].evidence_a_id, ev_mb.id)
        self.assertEqual(contradictions[0].evidence_b_id, ev_yolo.id)
        self.assertEqual(contradictions[0].severity, "HIGH")

    # -------------------------------------------------------------------------
    # Test 6: End-to-End Orchestrator Investigation Flow with YOLO Detection
    # -------------------------------------------------------------------------
    def test_6_end_to_end_orchestrator_investigation(self):
        ev_mb = EvidenceItem(
            id="e-mb-400", project_id=self.project_id, claim_id=self.claim.id, source_type="MB_RECORD",
            source_id="MB-402", observation="JE cert 400m", value=400.0, unit="meters", timestamp="2026-09-14",
            location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        self.db.save_evidence(ev_mb)

        raw_detection = self.detector.detect_image("storage://photo.jpg")
        self.adapter.adapt_vision_payload(self.project_id, self.claim, raw_detection)

        orchestrator = Orchestrator(self.db)
        res = orchestrator.run_investigation(self.project_id, self.claim.id)

        self.assertEqual(res["final_state"], InvestigationState.HUMAN_REVIEW_REQUIRED)
        self.assertEqual(res["contradiction_count"], 1)

    # -------------------------------------------------------------------------
    # Test 7: Citizen Evidence Graph Renders YOLO Node with Contradiction Edge
    # -------------------------------------------------------------------------
    def test_7_citizen_api_renders_yolo_node(self):
        ev_mb = EvidenceItem(
            id="e-mb-400", project_id=self.project_id, claim_id=self.claim.id, source_type="MB_RECORD",
            source_id="MB-402", observation="JE cert 400m", value=400.0, unit="meters", timestamp="2026-09-14",
            location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        self.db.save_evidence(ev_mb)

        raw_detection = self.detector.detect_image("storage://photo.jpg")
        ev_yolo = self.adapter.adapt_vision_payload(self.project_id, self.claim, raw_detection)

        # Run investigation to flag contradiction edge
        orchestrator = Orchestrator(self.db)
        orchestrator.run_investigation(self.project_id, self.claim.id)

        api = SentinelCitizenAPI(self.db)
        graph = api.get_evidence_graph(self.project_id)

        ev_nodes = graph["evidence"]
        yolo_node = next(e for e in ev_nodes if e["id"] == ev_yolo.id)
        self.assertEqual(yolo_node["source_type"], "GEO_PHOTO")
        self.assertEqual(yolo_node["relationship"], "CONTRADICTS")
        self.assertEqual(yolo_node["badge_icon"], "✕")
        self.assertIn("180.0 meters", yolo_node["observation"])


if __name__ == "__main__":
    unittest.main()
