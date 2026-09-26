"""
Contradiction Engine (Phase 3C - Spatial & Temporal Context Awareness).
Evaluates pairwise conflicts between evidence observations, validates DB evidence existence,
and enriches contradiction records with spatial and temporal relevance context.
"""
import uuid
from typing import List, Optional
from sentinel.types import EvidenceItem, ContradictionRecord, ConflictSeverity
from sentinel.engines.spatial_temporal_engine import SpatialTemporalEngine


class ContradictionEngine:
    def __init__(self, db=None, spatial_temporal_engine: Optional[SpatialTemporalEngine] = None):
        self.db = db
        self.st_engine = spatial_temporal_engine or SpatialTemporalEngine()

    def evaluate_contradictions(
        self,
        investigation_id: str,
        project_id: str,
        claim_id: Optional[str],
        evidence_items: List[EvidenceItem]
    ) -> List[ContradictionRecord]:
        contradictions = []
        already_paired = set()

        # Helper to validate DB existence
        def validate_db_existence(ev_a_id: str, ev_b_id: str):
            if self.db:
                db_ev = self.db.get_evidence_for_project(project_id)
                db_ids = {e.id for e in db_ev}
                if ev_a_id not in db_ids or ev_b_id not in db_ids:
                    raise ValueError(f"Invalid evidence reference: {ev_a_id} or {ev_b_id} does not exist in DB.")

        # 1. Evaluate explicit SUPPORTS vs CONTRADICTS pre-labeled items
        supported_items = [e for e in evidence_items if e.relationship == "SUPPORTS"]
        contradicting_items = [e for e in evidence_items if e.relationship == "CONTRADICTS"]

        for sup in supported_items:
            for con in contradicting_items:
                pair_key = tuple(sorted([sup.id, con.id]))
                if pair_key in already_paired:
                    continue
                already_paired.add(pair_key)
                validate_db_existence(sup.id, con.id)

                st_context = self.st_engine.evaluate_context(sup, con)

                severity = "HIGH" if (sup.reliability == "HIGH" and con.reliability == "HIGH") else "MEDIUM"
                conflict_record = ContradictionRecord(
                    id=str(uuid.uuid4()),
                    investigation_id=investigation_id,
                    project_id=project_id,
                    claim_id=claim_id,
                    evidence_a_id=sup.id,
                    evidence_b_id=con.id,
                    conflict_description=(
                        f"Direct physical contradiction: '{sup.source_type}' ({sup.observation}) "
                        f"conflicts with '{con.source_type}' ({con.observation}). "
                        f"Context: {st_context['summary']}"
                    ),
                    severity=severity,
                    status="UNRESOLVED",
                    metadata={
                        "variance_value_a": sup.value,
                        "variance_value_b": con.value,
                        "spatial_temporal_context": st_context
                    }
                )
                contradictions.append(conflict_record)

        # 2. Phase 2B.1 / 3C Analytical Layer: Evaluate physical measurement variance between observations
        measurement_items = [e for e in evidence_items if e.value is not None and e.source_type in ("MB_RECORD", "PHYSICAL_INSPECTION", "GEO_PHOTO")]
        for i in range(len(measurement_items)):
            for j in range(i + 1, len(measurement_items)):
                item_a = measurement_items[i]
                item_b = measurement_items[j]

                pair_key = tuple(sorted([item_a.id, item_b.id]))
                if pair_key in already_paired:
                    continue

                val_a = float(item_a.value)
                val_b = float(item_b.value)
                if val_a > 0 and abs(val_a - val_b) / max(val_a, val_b) > 0.10:
                    already_paired.add(pair_key)
                    validate_db_existence(item_a.id, item_b.id)

                    st_context = self.st_engine.evaluate_context(item_a, item_b)

                    severity = "HIGH" if (item_a.reliability == "HIGH" and item_b.reliability == "HIGH") else "MEDIUM"
                    conflict_record = ContradictionRecord(
                        id=str(uuid.uuid4()),
                        investigation_id=investigation_id,
                        project_id=project_id,
                        claim_id=claim_id,
                        evidence_a_id=item_a.id,
                        evidence_b_id=item_b.id,
                        conflict_description=(
                            f"Quantitative physical discrepancy detected by Contradiction Engine: "
                            f"'{item_a.source_type}' reports {val_a} {item_a.unit or ''}, while "
                            f"'{item_b.source_type}' reports {val_b} {item_b.unit or ''}. "
                            f"Context: {st_context['summary']}"
                        ),
                        severity=severity,
                        status="UNRESOLVED",
                        metadata={
                            "variance_value_a": val_a,
                            "variance_value_b": val_b,
                            "spatial_temporal_context": st_context
                        }
                    )
                    contradictions.append(conflict_record)

        return contradictions
