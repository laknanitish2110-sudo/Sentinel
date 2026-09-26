"""
Spatial and Temporal Evidence Engine for Sentinel (Phase 3C).
Evaluates spatial co-location and chronological relationships between evidence items.
STRICTLY NON-DECISIONAL: Context does NOT equal proof. Establishes contextual relevance
without overriding underlying evidence or generating financial/fraud judgments.
"""
import math
import uuid
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from sentinel.types import EvidenceItem


FORBIDDEN_JUDGMENTS = {
    "FRAUD",
    "FRAUDULENT",
    "INVALID_CLAIM",
    "PAYMENT_DENIAL",
    "GUILT",
    "VERIFIED_COMPLETION",
    "CLAIM_IS_FALSE",
    "PROJECT_PROGRESS_PERCENT"
}


class SpatialTemporalEngine:
    """Evaluates spatial and temporal context between evidence records and project timelines."""

    def __init__(self, spatial_threshold_km: float = 0.50):
        self.spatial_threshold_km = spatial_threshold_km

    def evaluate_context(
        self,
        evidence_a: EvidenceItem,
        evidence_b: EvidenceItem,
        project_start_date: Optional[str] = None,
        project_end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates spatial proximity and temporal alignment between two evidence items.
        Returns a structured contextual relevance payload.
        """
        spatial_rel, distance_km = self.evaluate_spatial_proximity(evidence_a.location, evidence_b.location)
        temporal_rel, time_delta_sec = self.evaluate_temporal_relationship(evidence_a.timestamp, evidence_b.timestamp)

        period_rel_a = self.evaluate_project_period_alignment(evidence_a.timestamp, project_start_date, project_end_date)
        period_rel_b = self.evaluate_project_period_alignment(evidence_b.timestamp, project_start_date, project_end_date)

        # Determine overall contextual relevance tag
        if spatial_rel == "SPATIALLY_RELEVANT" and temporal_rel != "TEMPORALLY_UNCERTAIN":
            contextual_tag = "SPATIALLY_AND_TEMPORALLY_CO_LOCATED"
        elif spatial_rel == "SPATIALLY_RELEVANT":
            contextual_tag = "SPATIALLY_RELEVANT"
        elif temporal_rel in ("EVIDENCE_BEFORE_RECORD", "EVIDENCE_AFTER_RECORD", "EVIDENCE_CO_TIMED"):
            contextual_tag = "TEMPORALLY_RELEVANT"
        elif spatial_rel == "SPATIALLY_UNCERTAIN" and temporal_rel == "TEMPORALLY_UNCERTAIN":
            contextual_tag = "INSUFFICIENT_CONTEXT"
        else:
            contextual_tag = "CONTEXTUALLY_DISTANT"

        context_payload = {
            "evaluation_id": f"ctx_{uuid.uuid4().hex[:8]}",
            "evidence_a_id": evidence_a.id,
            "evidence_b_id": evidence_b.id,
            "spatial_relationship": spatial_rel,
            "spatial_distance_km": round(distance_km, 4) if distance_km is not None else None,
            "temporal_relationship": temporal_rel,
            "time_delta_seconds": round(time_delta_sec, 2) if time_delta_sec is not None else None,
            "project_period_alignment_a": period_rel_a,
            "project_period_alignment_b": period_rel_b,
            "contextual_relevance": contextual_tag,
            "relationship_override": None,  # Invariant: Context NEVER overrides evidence to SUPPORTS/CONTRADICTS
            "summary": (
                f"Context analysis: Spatial={spatial_rel} ({distance_km:.2f}km if known), "
                f"Temporal={temporal_rel}. Contextual relevance tag: {contextual_tag}."
                if distance_km is not None else
                f"Context analysis: Spatial={spatial_rel}, Temporal={temporal_rel}. Tag: {contextual_tag}."
            )
        }

        self._validate_safety_invariants(context_payload["summary"])
        return context_payload

    def evaluate_spatial_proximity(
        self,
        loc_a: Optional[Dict[str, Any]],
        loc_b: Optional[Dict[str, Any]]
    ) -> Tuple[str, Optional[float]]:
        """
        Calculates Haversine distance between two location dictionaries.
        Returns ('SPATIALLY_UNCERTAIN', None) if GPS coordinates are missing.
        Do NOT guess or fabricate coordinates.
        """
        if not loc_a or not loc_b:
            return "SPATIALLY_UNCERTAIN", None

        lat1, lon1 = loc_a.get("latitude"), loc_a.get("longitude")
        lat2, lon2 = loc_b.get("latitude"), loc_b.get("longitude")

        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return "SPATIALLY_UNCERTAIN", None

        try:
            lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        except (ValueError, TypeError):
            return "SPATIALLY_UNCERTAIN", None

        # Haversine formula calculation
        R = 6371.0  # Earth radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        distance_km = R * c

        if distance_km <= self.spatial_threshold_km:
            return "SPATIALLY_RELEVANT", distance_km
        else:
            return "SPATIALLY_DISTANT", distance_km

    def evaluate_temporal_relationship(
        self,
        ts_a: Optional[str],
        ts_b: Optional[str]
    ) -> Tuple[str, Optional[float]]:
        """
        Evaluates chronological relationship between two ISO timestamp strings.
        Returns ('TEMPORALLY_UNCERTAIN', None) if any timestamp is missing or unparseable.
        """
        if not ts_a or not ts_b:
            return "TEMPORALLY_UNCERTAIN", None

        dt_a = self._parse_iso_timestamp(ts_a)
        dt_b = self._parse_iso_timestamp(ts_b)

        if not dt_a or not dt_b:
            return "TEMPORALLY_UNCERTAIN", None

        delta_sec = (dt_b - dt_a).total_seconds()

        if abs(delta_sec) <= 60:
            return "EVIDENCE_CO_TIMED", delta_sec
        elif delta_sec > 0:
            return "EVIDENCE_BEFORE_RECORD", delta_sec
        else:
            return "EVIDENCE_AFTER_RECORD", delta_sec

    def evaluate_project_period_alignment(
        self,
        ts: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> str:
        """Evaluates whether an evidence timestamp falls within sanctioned project timeline."""
        if not ts or not start_date:
            return "TEMPORALLY_UNCERTAIN"

        dt_ev = self._parse_iso_timestamp(ts)
        dt_start = self._parse_iso_timestamp(start_date)
        dt_end = self._parse_iso_timestamp(end_date) if end_date else None

        if not dt_ev or not dt_start:
            return "TEMPORALLY_UNCERTAIN"

        if dt_ev < dt_start:
            return "EVIDENCE_PRE_PROJECT"

        if dt_end and dt_ev > dt_end:
            return "EVIDENCE_POST_PROJECT"

        return "EVIDENCE_WITHIN_PROJECT_PERIOD"

    def _parse_iso_timestamp(self, ts_str: str) -> Optional[datetime]:
        """Parses ISO timestamp strings safely."""
        if not ts_str:
            return None
        cleaned = ts_str.replace("Z", "+00:00")
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d"
        ):
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue
        return None

    def _validate_safety_invariants(self, text: str):
        """Enforces safety invariant preventing financial, legal, or fraud judgments."""
        text_upper = text.upper()
        for forbidden in FORBIDDEN_JUDGMENTS:
            if forbidden in text_upper:
                raise ValueError(
                    f"SpatialTemporalEngine Safety Violation: Output contains forbidden term '{forbidden}'"
                )
