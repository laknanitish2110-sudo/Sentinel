"""
SENTINEL Phase 4B Test Suite — Real Construction Evidence Evaluation.
Verifies VisionEvaluator dataset analysis, taxonomy primitive coverage mapping,
unsupported class filtering, and perception-only NEUTRAL evidence bounds.
"""
import os
import unittest

from sentinel.vision.evaluator import VisionEvaluator
from sentinel.vision.taxonomy import VisualPrimitive


class TestSentinelPhase4B(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.eval_dir = os.path.abspath("data/vision_eval")
        cls.evaluator = VisionEvaluator(model_name="yolov8n.pt", confidence_threshold=0.20)

    def test_1_evaluator_dataset_analysis(self):
        """Verify VisionEvaluator analyzes data/vision_eval dataset images."""
        report = self.evaluator.evaluate_dataset(self.eval_dir)
        self.assertEqual(report["model_name"], "yolov8n.pt")
        self.assertIn("primitive_coverage", report)
        self.assertGreaterEqual(report["sample_count"], 1)

    def test_2_taxonomy_coverage_partially_supported_primitives(self):
        """Verify worker and construction_equipment are marked PARTIALLY_SUPPORTED via COCO mapping."""
        report = self.evaluator.evaluate_dataset(self.eval_dir)
        coverage = report["primitive_coverage"]

        self.assertEqual(coverage["worker"]["status"], "PARTIALLY_SUPPORTED")
        self.assertEqual(coverage["construction_equipment"]["status"], "PARTIALLY_SUPPORTED")

    def test_3_taxonomy_coverage_unsupported_primitives(self):
        """Verify pipe, trench, manhole, excavator, etc., are explicitly marked NOT_SUPPORTED."""
        report = self.evaluator.evaluate_dataset(self.eval_dir)
        coverage = report["primitive_coverage"]

        unsupported_keys = [
            "pipe", "trench", "manhole", "excavator", "concrete",
            "gravel", "soil", "material_stack", "road_surface"
        ]

        for key in unsupported_keys:
            self.assertEqual(
                coverage[key]["status"],
                "NOT_SUPPORTED",
                f"Primitive '{key}' must be NOT_SUPPORTED for generic COCO model"
            )

    def test_4_event_interpreter_provenance_and_neutral_bounds(self):
        """Verify evaluated sample events preserve NEUTRAL relationship and uncertainty score."""
        report = self.evaluator.evaluate_dataset(self.eval_dir)
        for sample in report["sample_results"]:
            for event in sample["interpreted_events"]:
                self.assertEqual(event["relationship"], "NEUTRAL")
                self.assertIn("uncertainty_score", event)
                self.assertIn("model_checkpoint_identifier", event)


if __name__ == "__main__":
    unittest.main()
