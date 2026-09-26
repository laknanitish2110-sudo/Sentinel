"""
SENTINEL Phase 3A.1 Test Suite — Real Pretrained Ultralytics YOLO Vision Inference.
Verifies real tensor inference, bounding box preservation, perception-only NEUTRAL boundary,
and Evidence Contract normalization.
"""
import os
import unittest
from PIL import Image, ImageDraw

from sentinel.vision.yolo_detector import YOLODetector, ULTRALYTICS_AVAILABLE
from sentinel.vision.adapter import VisionEvidenceAdapter
from sentinel.db import SentinelDB
from sentinel.types import Project, Claim


class TestSentinelPhase3A1(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_img_path = os.path.abspath("test_phase3a1_image.jpg")
        img = Image.new("RGB", (640, 480), color=(180, 200, 220))
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 250, 250], fill=(200, 50, 50), outline=(0, 0, 0))
        draw.ellipse([300, 100, 500, 300], fill=(50, 200, 50), outline=(0, 0, 0))
        img.save(cls.test_img_path, "JPEG")

        cls.db = SentinelDB()
        cls.project = Project(
            id="proj_phase3a1_test",
            code="PRJ-3A1",
            name="Phase 3A1 Real Inference Project",
            description="Test project for real vision model inference",
            sanctioned_amount=1000000.0,
            released_amount=500000.0
        )
        cls.db.save_project(cls.project)

        cls.claim = Claim(
            id="clm_phase3a1_test",
            project_id=cls.project.id,
            claim_ref="CLM-3A1-001",
            claimed_by="Test Contractor",
            claim_type="PHYSICAL_QUANTITY",
            description="Claimed 250m drainage pipe",
            claimed_value=250.0,
            unit="meters",
            claim_date="2026-09-20"
        )
        cls.db.save_claim(cls.claim)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_img_path):
            os.remove(cls.test_img_path)

    def test_1_ultralytics_availability_and_detector_instantiation(self):
        """Verify ultralytics module can be imported and YOLODetector instantiated."""
        self.assertTrue(ULTRALYTICS_AVAILABLE, "Ultralytics module must be installed and importable")
        detector = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.25)
        self.assertEqual(detector.model_name, "yolov8n.pt")
        self.assertIsNotNone(detector._yolo_model, "YOLO model instance should be initialized")

    def test_2_real_image_tensor_inference_and_detections(self):
        """Verify real image inference returns structured detection payload with bounding boxes."""
        detector = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.25)
        payload = detector.detect_image(self.test_img_path)

        self.assertEqual(payload["inference_type"], "real_ultralytics_tensor_inference")
        self.assertEqual(payload["image_width"], 640)
        self.assertEqual(payload["image_height"], 480)
        self.assertIn("bounding_boxes", payload)
        self.assertGreaterEqual(len(payload["bounding_boxes"]), 1)

        box = payload["bounding_boxes"][0]
        self.assertIn("class", box)
        self.assertIn("confidence", box)
        self.assertIn("box", box)
        self.assertEqual(len(box["box"]), 4)

    def test_3_bounding_boxes_and_confidence_preservation(self):
        """Verify bounding box coordinates and confidence scores are preserved accurately."""
        detector = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.10)
        payload = detector.detect_image(self.test_img_path)

        conf = payload["confidence"]
        self.assertGreater(conf, 0.0)
        self.assertLessEqual(conf, 1.0)

        for box in payload["bounding_boxes"]:
            ymin, xmin, ymax, xmax = box["box"]
            self.assertGreaterEqual(ymin, 0)
            self.assertGreaterEqual(xmin, 0)
            self.assertGreater(ymax, ymin)
            self.assertGreater(xmax, xmin)

    def test_4_adapter_converts_real_detections_to_neutral_evidence(self):
        """Verify VisionEvidenceAdapter transforms real detections into NEUTRAL evidence."""
        detector = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.25)
        payload = detector.detect_image(self.test_img_path)

        adapter = VisionEvidenceAdapter(db=self.db)
        evidence = adapter.adapt_vision_payload(
            project_id=self.project.id,
            claim=self.claim,
            vision_payload=payload,
            source_id="YOLOv8n-UNIT-TEST-001"
        )

        self.assertEqual(evidence.relationship, "NEUTRAL", "Raw vision evidence must always be NEUTRAL")
        self.assertEqual(evidence.source_type, "GEO_PHOTO")
        self.assertIn("bounding_boxes", evidence.metadata)
        self.assertEqual(evidence.metadata["vision_model"], "yolov8n.pt")

    def test_5_detector_does_not_generate_contradiction(self):
        """Verify detector itself emits zero decision flags, contradiction terms, or fraud accusations."""
        detector = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.25)
        payload = detector.detect_image(self.test_img_path)

        forbidden_terms = ["SUPPORTS", "CONTRADICTS", "FRAUD", "INVALID", "DENIED", "REJECTED"]
        obs_upper = payload["observation"].upper()

        for term in forbidden_terms:
            self.assertNotIn(term, obs_upper, f"Detector payload observation must not contain '{term}'")


if __name__ == "__main__":
    unittest.main()
