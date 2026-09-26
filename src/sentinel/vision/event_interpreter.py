"""
SENTINEL Construction Perception Event Interpreter (Phase 3B).
Converts raw vision observations into structured, uncertain perception events,
preserving complete model provenance and perception-only bounds.
"""
import uuid
from typing import Dict, Any, List, Optional
from sentinel.vision.taxonomy import (
    VisualPrimitive,
    PerceptionEvent,
    TAXONOMY_VERSION,
    CLASS_PRIMITIVE_MAPPING,
    PRIMITIVE_EVENT_MAPPING,
    FORBIDDEN_JUDGMENT_TERMS
)


INTERPRETER_VERSION = "v3B-perception-interpreter-1.0"


class ConstructionEventInterpreter:
    """Interprets raw visual detections into structured perception events with provenance."""

    def __init__(self, confidence_threshold: float = 0.25):
        self.confidence_threshold = confidence_threshold
        self.version = INTERPRETER_VERSION
        self.taxonomy_version = TAXONOMY_VERSION

    def interpret_vision_evidence(
        self,
        vision_payload: Dict[str, Any],
        source_evidence_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Transforms raw YOLO detection payload into structured perception event records.
        Preserves provenance, model confidence, bounding box coordinates, and metadata.
        STRICTLY PERCEPTION-ONLY: Emits relationship = 'NEUTRAL'.
        """
        evidence_id = source_evidence_id or vision_payload.get("evidence_id") or str(uuid.uuid4())
        boxes = vision_payload.get("bounding_boxes", [])
        vision_model = vision_payload.get("vision_model", "yolov8n.pt")
        img_width = vision_payload.get("image_width", 1920)
        img_height = vision_payload.get("image_height", 1080)
        timestamp = vision_payload.get("exif", {}).get("timestamp", "2026-09-18T09:15:00Z")
        location = vision_payload.get("location")

        events: List[Dict[str, Any]] = []

        for box in boxes:
            raw_class = box.get("class", "").lower()
            confidence = box.get("confidence", 0.50)
            bbox = box.get("box", [0, 0, 0, 0])

            if confidence < self.confidence_threshold:
                continue

            # Step 4: Do NOT fabricate construction classes for unsupported COCO labels
            primitive = CLASS_PRIMITIVE_MAPPING.get(raw_class)
            if not primitive:
                # Unsupported class (e.g. 'kite', 'dog', 'bottle').
                # Leave event unavailable rather than fabricating false construction primitives.
                continue

            event_type = PRIMITIVE_EVENT_MAPPING.get(primitive, PerceptionEvent.POSSIBLE_CONSTRUCTION_ACTIVITY)
            
            # Explicit uncertainty representation
            uncertainty_score = round(1.0 - confidence, 4)

            observation_description = (
                f"Perception interpreter ({self.version}) identified {event_type.value} "
                f"from visual primitive '{primitive.value}' (raw model class '{raw_class}', conf: {confidence:.2f})."
            )

            # Safety check: Verify non-accusatory / forbidden terms
            self._validate_non_accusatory(observation_description)

            event_record = {
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "source_evidence_id": evidence_id,
                "perception_event": event_type.value,
                "visual_primitive": primitive.value,
                "original_model_class": raw_class,
                "model_confidence": confidence,
                "uncertainty_score": uncertainty_score,
                "bounding_box": bbox,
                "image_dimensions": f"{img_width}x{img_height}",
                "model_checkpoint_identifier": vision_model,
                "timestamp": timestamp,
                "location": location,
                "interpreter_version": self.version,
                "taxonomy_version": self.taxonomy_version,
                "relationship": "NEUTRAL",
                "observation_description": observation_description
            }

            events.append(event_record)

        return events

    def _validate_non_accusatory(self, text: str):
        """Enforces safety invariant preventing financial, legal, or fraud judgments."""
        text_upper = text.upper()
        for forbidden in FORBIDDEN_JUDGMENT_TERMS:
            if forbidden in text_upper:
                raise ValueError(
                    f"Perception Interpreter Safety Failure: Text contains forbidden judgment term '{forbidden}'"
                )
