"""
SENTINEL Phase 4B.1 Test Suite — Genuine Construction Evidence Validation & Perception Semantics Corrections.
Verifies real-world evaluation dataset loading, provenance documentation, authentic licensing,
actual YOLO output schema, unsupported primitive protection, conservative perception event mapping,
perception-only NEUTRAL relationship bounds, model confidence preservation, and evidence ID preservation.
"""
import os
import unittest
from PIL import Image

from sentinel.vision.yolo_detector import YOLODetector
from sentinel.vision.event_interpreter import ConstructionEventInterpreter
from sentinel.vision.taxonomy import CLASS_PRIMITIVE_MAPPING, PRIMITIVE_EVENT_MAPPING, VisualPrimitive, PerceptionEvent


class TestSentinelPhase4B1(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.real_eval_dir = os.path.abspath("data/vision_eval_real")
        cls.readme_path = os.path.join(cls.real_eval_dir, "README.md")
        cls.detector = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.25)
        cls.interpreter = ConstructionEventInterpreter(confidence_threshold=0.25)

    def test_1_real_evaluation_dataset_loading(self):
        """Verify real evaluation directory exists and contains at least 3 valid JPEG images."""
        self.assertTrue(os.path.exists(self.real_eval_dir), "data/vision_eval_real directory must exist")
        self.assertTrue(os.path.isdir(self.real_eval_dir), "data/vision_eval_real must be a directory")

        files = [f for f in os.listdir(self.real_eval_dir) if f.endswith(".jpg")]
        self.assertGreaterEqual(len(files), 3, "data/vision_eval_real must contain at least 3 real image files")

        for f in files:
            img_path = os.path.join(self.real_eval_dir, f)
            with Image.open(img_path) as img:
                self.assertGreater(img.width, 0)
                self.assertGreater(img.height, 0)

    def test_2_provenance_documentation_presence(self):
        """Verify README.md exists in data/vision_eval_real and contains detailed provenance for each sample."""
        self.assertTrue(os.path.exists(self.readme_path), "data/vision_eval_real/README.md must exist")
        
        with open(self.readme_path, "r", encoding="utf-8") as f:
            readme_text = f.read()

        self.assertIn("real_eval_01_concrete_pump_truck.jpg", readme_text)
        self.assertIn("real_eval_02_construction_works_osaka.jpg", readme_text)
        self.assertIn("real_eval_03_construction_labour_workers.jpg", readme_text)
        self.assertIn("CC BY-SA 4.0", readme_text)
        self.assertIn("Public Domain", readme_text)
        self.assertIn("Canonical Page", readme_text)
        self.assertIn("Attribution Requirement", readme_text)

    def test_3_actual_yolo_output_schema(self):
        """Verify YOLODetector inference on real images produces exact raw vision output schema."""
        sample_image = os.path.join(self.real_eval_dir, "real_eval_02_construction_works_osaka.jpg")
        dets = self.detector.detect_image(sample_image)

        expected_keys = [
            "raw_image_uri", "vision_model", "inference_type",
            "image_width", "image_height", "observation",
            "confidence", "location", "exif", "bounding_boxes"
        ]
        for key in expected_keys:
            self.assertIn(key, dets, f"YOLO detection payload must contain schema key '{key}'")

        self.assertEqual(dets["raw_image_uri"], sample_image)
        self.assertEqual(dets["vision_model"], "yolov8n.pt")
        self.assertIsInstance(dets["bounding_boxes"], list)

    def test_4_unsupported_primitive_protection(self):
        """Verify ConstructionEventInterpreter does not fabricate construction primitives for unsupported COCO classes."""
        mock_payload = {
            "evidence_id": "test_unsupported_ev",
            "vision_model": "yolov8n.pt",
            "image_width": 1920,
            "image_height": 1080,
            "bounding_boxes": [
                {"class": "car", "confidence": 0.85, "box": [10, 10, 50, 50]},
                {"class": "umbrella", "confidence": 0.75, "box": [60, 60, 100, 100]},
                {"class": "person", "confidence": 0.90, "box": [110, 110, 200, 200]}
            ]
        }

        events = self.interpreter.interpret_vision_evidence(mock_payload, source_evidence_id="test_unsupported_ev")
        
        self.assertEqual(len(events), 1, "Only supported COCO classes should yield events")
        self.assertEqual(events[0]["original_model_class"], "person")
        self.assertEqual(events[0]["visual_primitive"], "worker")

        self.assertNotIn("car", CLASS_PRIMITIVE_MAPPING)
        self.assertNotIn("umbrella", CLASS_PRIMITIVE_MAPPING)

    def test_5_event_interpreter_neutral_constraint(self):
        """Verify all events generated on real evaluation images strictly adhere to relationship == 'NEUTRAL'."""
        sample_image = os.path.join(self.real_eval_dir, "real_eval_02_construction_works_osaka.jpg")
        dets = self.detector.detect_image(sample_image)
        events = self.interpreter.interpret_vision_evidence(dets, source_evidence_id="ev_osaka_real")

        self.assertGreaterEqual(len(events), 1, "Real image must produce at least one event")
        for evt in events:
            self.assertEqual(evt["relationship"], "NEUTRAL", "Event relationship must be perception-only NEUTRAL")
            self.assertIn("uncertainty_score", evt)
            self.assertIn("observation_description", evt)
            
            desc_upper = evt["observation_description"].upper()
            forbidden = ["COMPLETED_PROJECT", "FRAUD", "INVALID_CLAIM", "PAYMENT_DENIAL", "VERIFIED_COMPLETION"]
            for f_term in forbidden:
                self.assertNotIn(f_term, desc_upper, f"Description must not contain forbidden term '{f_term}'")

    def test_6_confidence_preservation(self):
        """Verify model confidence score is preserved exactly from raw YOLO output to event record."""
        sample_image = os.path.join(self.real_eval_dir, "real_eval_03_construction_labour_workers.jpg")
        dets = self.detector.detect_image(sample_image)
        events = self.interpreter.interpret_vision_evidence(dets, source_evidence_id="ev_labour_real")

        person_boxes = [b for b in dets["bounding_boxes"] if b["class"] == "person"]
        person_events = [e for e in events if e["original_model_class"] == "person"]

        self.assertEqual(len(person_boxes), len(person_events))
        for box, evt in zip(person_boxes, person_events):
            self.assertEqual(evt["model_confidence"], box["confidence"])

    def test_7_source_evidence_preservation(self):
        """Verify source evidence ID is preserved in interpreted perception events."""
        test_ev_id = "evidence_provenance_id_999"
        sample_image = os.path.join(self.real_eval_dir, "real_eval_01_concrete_pump_truck.jpg")
        dets = self.detector.detect_image(sample_image)
        events = self.interpreter.interpret_vision_evidence(dets, source_evidence_id=test_ev_id)

        self.assertGreaterEqual(len(events), 1)
        for evt in events:
            self.assertEqual(evt["source_evidence_id"], test_ev_id)

    def test_8_truck_detection_cannot_emit_material_delivery(self):
        """Verify truck detection produces conservative construction_activity event and NEVER material_delivery alone."""
        truck_payload = {
            "evidence_id": "ev_truck_semantics_test",
            "vision_model": "yolov8n.pt",
            "image_width": 1920,
            "image_height": 1080,
            "bounding_boxes": [
                {"class": "truck", "confidence": 0.88, "box": [100, 200, 500, 800]}
            ]
        }
        events = self.interpreter.interpret_vision_evidence(truck_payload)
        self.assertEqual(len(events), 1)
        truck_evt = events[0]

        # Must map to conservative possible_construction_activity
        self.assertEqual(truck_evt["perception_event"], PerceptionEvent.POSSIBLE_CONSTRUCTION_ACTIVITY.value)
        self.assertNotEqual(truck_evt["perception_event"], "possible_material_delivery")
        self.assertNotIn("material_delivery", truck_evt["perception_event"])
        self.assertNotIn("material_delivered", truck_evt["observation_description"])

    def test_9_person_detection_partial_worker_evidence(self):
        """Verify COCO person detection maps to worker primitive under PARTIALLY_SUPPORTED semantics."""
        person_payload = {
            "evidence_id": "ev_person_semantics_test",
            "vision_model": "yolov8n.pt",
            "image_width": 1920,
            "image_height": 1080,
            "bounding_boxes": [
                {"class": "person", "confidence": 0.85, "box": [50, 50, 200, 200]}
            ]
        }
        events = self.interpreter.interpret_vision_evidence(person_payload)
        self.assertEqual(len(events), 1)
        person_evt = events[0]

        self.assertEqual(person_evt["visual_primitive"], VisualPrimitive.WORKER.value)
        self.assertEqual(person_evt["perception_event"], PerceptionEvent.POSSIBLE_CONSTRUCTION_ACTIVITY.value)
        self.assertEqual(person_evt["relationship"], "NEUTRAL")

    def test_10_licensing_provenance_intact(self):
        """Verify README.md contains authentic author, CC BY-SA 4.0, and Public Domain provenance records."""
        with open(self.readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Steve Pivnick, U.S. Air Force", content)
        self.assertIn("Editorq35", content)
        self.assertIn("PatInver", content)
        self.assertIn("CC BY-SA 4.0", content)
        self.assertIn("Public Domain", content)


if __name__ == "__main__":
    unittest.main()
