"""
SENTINEL Phase 3B Test Suite — Construction Perception Layer.
Verifies taxonomy mapping, explicit uncertainty representation, provenance preservation,
unsupported class filtering, perception-only NEUTRAL bounds, and non-accusatory safety bounds.
"""
import unittest
from typing import Dict, Any

from sentinel.vision.event_interpreter import ConstructionEventInterpreter
from sentinel.vision.taxonomy import VisualPrimitive, PerceptionEvent, FORBIDDEN_JUDGMENT_TERMS


class TestSentinelPhase3B(unittest.TestCase):

    def setUp(self):
        self.interpreter = ConstructionEventInterpreter(confidence_threshold=0.20)
        self.sample_yolo_payload: Dict[str, Any] = {
            "evidence_id": "evi_test_phase3b_001",
            "vision_model": "yolov8n.pt",
            "image_width": 1920,
            "image_height": 1080,
            "observation": "Pretrained Ultralytics YOLO model (yolov8n.pt) detected objects.",
            "location": {"latitude": 12.972, "longitude": 77.595},
            "exif": {"timestamp": "2026-09-20T10:00:00Z"},
            "bounding_boxes": [
                {
                    "class": "truck",
                    "confidence": 0.88,
                    "box": [100, 200, 500, 800]
                },
                {
                    "class": "person",
                    "confidence": 0.92,
                    "box": [50, 60, 150, 100]
                },
                {
                    "class": "kite",  # Generic unsupported COCO class
                    "confidence": 0.95,
                    "box": [10, 20, 30, 40]
                }
            ]
        }

    def test_1_generic_yolo_observation_preserved(self):
        """Verify original YOLO observation and raw model payload are preserved in source evidence."""
        events = self.interpreter.interpret_vision_evidence(
            self.sample_yolo_payload, source_evidence_id="evi_test_phase3b_001"
        )
        self.assertGreater(len(events), 0)
        for evt in events:
            self.assertEqual(evt["source_evidence_id"], "evi_test_phase3b_001")
            self.assertEqual(evt["model_checkpoint_identifier"], "yolov8n.pt")

    def test_2_unsupported_construction_class_not_fabricated(self):
        """Verify unsupported generic COCO class (e.g., 'kite') is NOT fabricated into false construction primitive."""
        events = self.interpreter.interpret_vision_evidence(self.sample_yolo_payload)
        classes_extracted = [e["original_model_class"] for e in events]
        self.assertNotIn("kite", classes_extracted, "Unsupported class 'kite' must not produce a construction event")

    def test_3_supported_mapping_produces_possible_perception_event(self):
        """Verify supported mapping (e.g. 'truck' -> 'construction_equipment') produces a conservative 'possible_' event."""
        events = self.interpreter.interpret_vision_evidence(self.sample_yolo_payload)
        event_types = [e["perception_event"] for e in events]

        # 'truck' and 'person' map to conservative possible_construction_activity event
        self.assertIn("possible_construction_activity", event_types)
        self.assertNotIn("possible_material_delivery", event_types, "Truck detection alone must NOT emit possible_material_delivery")
        
        # Verify 'possible_' uncertainty prefix is present on all event types
        for evt in events:
            self.assertTrue(evt["perception_event"].startswith("possible_"), "Event must represent explicit uncertainty")

    def test_4_event_preserves_source_evidence_id(self):
        """Verify interpreted perception event links back to original evidence ID."""
        events = self.interpreter.interpret_vision_evidence(
            self.sample_yolo_payload, source_evidence_id="evi_custom_999"
        )
        self.assertEqual(events[0]["source_evidence_id"], "evi_custom_999")

    def test_5_event_preserves_model_confidence_and_uncertainty(self):
        """Verify model confidence and explicit uncertainty score (1 - confidence) are preserved."""
        events = self.interpreter.interpret_vision_evidence(self.sample_yolo_payload)
        truck_event = next(e for e in events if e["original_model_class"] == "truck")

        self.assertEqual(truck_event["model_confidence"], 0.88)
        self.assertAlmostEqual(truck_event["uncertainty_score"], 0.12, places=4)

    def test_6_event_preserves_full_provenance(self):
        """Verify event preserves full provenance: bounding box, resolution, model checkpoint, timestamp, location."""
        events = self.interpreter.interpret_vision_evidence(self.sample_yolo_payload)
        evt = events[0]

        self.assertEqual(evt["bounding_box"], [100, 200, 500, 800])
        self.assertEqual(evt["image_dimensions"], "1920x1080")
        self.assertEqual(evt["model_checkpoint_identifier"], "yolov8n.pt")
        self.assertEqual(evt["timestamp"], "2026-09-20T10:00:00Z")
        self.assertEqual(evt["location"], {"latitude": 12.972, "longitude": 77.595})
        self.assertIn("interpreter_version", evt)

    def test_7_event_remains_strictly_neutral(self):
        """Verify interpreted event relationship remains strictly NEUTRAL."""
        events = self.interpreter.interpret_vision_evidence(self.sample_yolo_payload)
        for evt in events:
            self.assertEqual(evt["relationship"], "NEUTRAL", "Event relationship must be strictly NEUTRAL")

    def test_8_interpreter_cannot_emit_forbidden_judgments(self):
        """Verify interpreter rejects any text containing forbidden financial/legal/fraud judgment terms."""
        with self.assertRaises(ValueError):
            self.interpreter._validate_non_accusatory("Project is FRAUDULENT and claim is false")

        with self.assertRaises(ValueError):
            self.interpreter._validate_non_accusatory("Verified VERIFIED_COMPLETION 100%")


if __name__ == "__main__":
    unittest.main()
