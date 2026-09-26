"""
Vision Evidence Adapter for Sentinel (Phase 2B.1 - Perception-Only Correction).
Normalizes raw computer vision outputs into standard Evidence Contract observations.
STRICTLY PERCEPTION-ONLY: Does NOT make analytical judgements (SUPPORTS/CONTRADICTS).
Decision & relationship analysis is deferred exclusively to downstream Contradiction Engine & Decision Engine.
"""
import uuid
from typing import Dict, Any, Optional
from sentinel.types import EvidenceItem, Claim
from sentinel.db import SentinelDB


class VisionEvidenceAdapter:
    """Adapts raw computer vision model outputs to the Sentinel Evidence Contract."""

    def __init__(self, db: Optional[SentinelDB] = None):
        self.db = db

    def adapt_vision_payload(
        self,
        project_id: str,
        claim: Optional[Claim],
        vision_payload: Dict[str, Any],
        source_id: Optional[str] = None
    ) -> EvidenceItem:
        """
        Transforms raw vision payload into a normalized EvidenceItem.
        PERCEPTION-ONLY: Sets relationship to 'NEUTRAL' (or 'INSUFFICIENT' if low confidence).
        Does NOT evaluate support vs contradiction against claims.
        """
        evidence_id = str(uuid.uuid4())
        claim_id = claim.id if claim else None
        detected_val = vision_payload.get("primary_detected_value")
        unit = vision_payload.get("unit", "meters")
        confidence = vision_payload.get("confidence", 0.90)

        # Perception-Only Boundary: Raw vision is NEUTRAL (or INSUFFICIENT if low confidence)
        relationship = "INSUFFICIENT" if confidence < 0.50 else "NEUTRAL"

        metadata = {
            "vision_model": vision_payload.get("vision_model", "yolov8-drainage-v1"),
            "raw_image_uri": vision_payload.get("raw_image_uri"),
            "bounding_boxes": vision_payload.get("bounding_boxes", []),
            "exif": vision_payload.get("exif", {}),
            "staged_pipe_count": vision_payload.get("staged_pipe_count", 0),
            "adapter_version": "v2B.1-perception-only"
        }

        evidence_item = EvidenceItem(
            id=evidence_id,
            project_id=project_id,
            claim_id=claim_id,
            source_type="GEO_PHOTO",
            source_id=source_id or f"PHOTO-VISION-{uuid.uuid4().hex[:8].upper()}",
            observation=vision_payload.get("observation", "Vision detection completed."),
            value=detected_val,
            unit=unit,
            timestamp=vision_payload.get("exif", {}).get("timestamp", "2026-09-18T09:15:00Z"),
            location=vision_payload.get("location"),
            confidence=confidence,
            reliability="HIGH" if confidence >= 0.80 else "MEDIUM",
            relationship=relationship,
            metadata=metadata
        )

        if self.db:
            self.db.save_evidence(evidence_item)

        return evidence_item
