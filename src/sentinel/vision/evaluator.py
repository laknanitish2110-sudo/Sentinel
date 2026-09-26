"""
SENTINEL Vision Perception Evaluator (Phase 4B).
Evaluates real model coverage against construction taxonomy primitives,
measuring genuine COCO detection capability versus specialized civil engineering requirements.
"""
import os
from typing import Dict, Any, List, Optional
from sentinel.vision.yolo_detector import YOLODetector
from sentinel.vision.event_interpreter import ConstructionEventInterpreter
from sentinel.vision.taxonomy import (
    VisualPrimitive,
    CLASS_PRIMITIVE_MAPPING,
    TAXONOMY_VERSION
)


class VisionEvaluator:
    """Evaluates pretrained YOLO model coverage against the construction perception taxonomy."""

    def __init__(self, model_name: str = "yolov8n.pt", confidence_threshold: float = 0.20):
        self.detector = YOLODetector(model_name=model_name, confidence_threshold=confidence_threshold)
        self.interpreter = ConstructionEventInterpreter(confidence_threshold=confidence_threshold)

    def evaluate_dataset(self, dataset_dir: str) -> Dict[str, Any]:
        """
        Runs evaluation over all images in the specified dataset directory.
        Returns detailed raw detections, interpreted events, and primitive coverage metrics.
        """
        if not os.path.exists(dataset_dir):
            raise FileNotFoundError(f"Evaluation dataset directory not found: {dataset_dir}")

        image_extensions = (".jpg", ".jpeg", ".png")
        image_files = [
            os.path.join(dataset_dir, f)
            for f in os.listdir(dataset_dir)
            if f.lower().endswith(image_extensions)
        ]

        sample_results = []
        all_detected_coco_classes = set()

        for img_path in sorted(image_files):
            raw_payload = self.detector.detect_image(img_path)
            events = self.interpreter.interpret_vision_evidence(raw_payload)

            for box in raw_payload.get("bounding_boxes", []):
                all_detected_coco_classes.add(box.get("class", ""))

            sample_results.append({
                "image_path": img_path,
                "filename": os.path.basename(img_path),
                "raw_detections": raw_payload,
                "interpreted_events": events,
                "detection_count": len(raw_payload.get("bounding_boxes", [])),
                "event_count": len(events)
            })

        primitive_coverage = self._compute_taxonomy_coverage(all_detected_coco_classes, sample_results)

        return {
            "taxonomy_version": TAXONOMY_VERSION,
            "model_name": self.detector.model_name,
            "sample_count": len(image_files),
            "sample_results": sample_results,
            "detected_coco_classes": sorted(list(all_detected_coco_classes)),
            "primitive_coverage": primitive_coverage
        }

    def _compute_taxonomy_coverage(
        self,
        detected_coco_classes: set,
        sample_results: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Computes SUPPORTED / PARTIALLY_SUPPORTED / NOT_SUPPORTED status for each visual primitive."""
        coverage: Dict[str, Dict[str, Any]] = {}

        # Mappings from COCO capability to primitives
        partially_supported_primitives = {
            VisualPrimitive.WORKER.value: ("person", "COCO 'person' class detects human presence on site; mapped to 'worker'"),
            VisualPrimitive.CONSTRUCTION_EQUIPMENT.value: ("truck", "COCO 'truck' class detects heavy vehicle presence; mapped to 'construction_equipment'")
        }

        for primitive in VisualPrimitive:
            prim_key = primitive.value
            mapping_coco = [cls for cls, prim in CLASS_PRIMITIVE_MAPPING.items() if prim == primitive]

            if prim_key in partially_supported_primitives:
                coco_cls, explanation = partially_supported_primitives[prim_key]
                has_detected = coco_cls in detected_coco_classes or any(coco_cls in r["detected_coco_classes"] for r in sample_results if "detected_coco_classes" in r)
                coverage[prim_key] = {
                    "primitive": prim_key,
                    "status": "PARTIALLY_SUPPORTED",
                    "evidence": explanation,
                    "mapped_coco_classes": mapping_coco,
                    "detected_coco_matches": [coco_cls] if has_detected else []
                }
            else:
                coverage[prim_key] = {
                    "primitive": prim_key,
                    "status": "NOT_SUPPORTED",
                    "evidence": f"Pretrained COCO model ({self.detector.model_name}) lacks detection capability for '{prim_key}'",
                    "mapped_coco_classes": mapping_coco,
                    "detected_coco_matches": []
                }

        return coverage
