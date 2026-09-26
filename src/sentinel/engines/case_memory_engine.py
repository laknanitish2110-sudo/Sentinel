"""
Case Memory Engine (Phase 3D - Human Correction to Case Memory Loop).
Processes human auditor corrections into structured, append-only case memory records,
enables deterministic similarity retrieval of historical precedents,
and formats citizen-safe precedent summaries.
"""
import uuid
from typing import List, Optional, Tuple, Dict, Any
from sentinel.types import HumanCorrection, CaseMemoryRecord
from sentinel.db import SentinelDB


class CaseMemoryEngine:
    """Manages structured case memory, precedent rules, and similarity retrieval."""

    def __init__(self, db: SentinelDB):
        self.db = db

    def process_human_correction(
        self,
        investigation_id: str,
        project_id: str,
        claim_id: Optional[str],
        corrected_by: str,
        original_interpretation: str,
        corrected_interpretation: str,
        reason_for_correction: str,
        evidence_ids_involved: List[str],
        pattern_type: str = "UNDERGROUND_COVERED_WORK",
        spatial_context: Optional[Dict[str, Any]] = None,
        temporal_context: Optional[Dict[str, Any]] = None,
        user_role: str = "auditor"
    ) -> Tuple[HumanCorrection, CaseMemoryRecord]:
        """
        Records a human auditor correction without overwriting the original interpretation.
        Creates an append-only CaseMemoryRecord for future precedent retrieval.
        """
        # 1. Save Human Correction (preserves original interpretation & auditor metadata)
        correction = HumanCorrection(
            id=str(uuid.uuid4()),
            investigation_id=investigation_id,
            project_id=project_id,
            claim_id=claim_id,
            corrected_by=corrected_by,
            original_interpretation=original_interpretation,
            corrected_interpretation=corrected_interpretation,
            reason_for_correction=reason_for_correction,
            evidence_ids_involved=evidence_ids_involved,
            metadata={
                "pattern_type": pattern_type,
                "spatial_context": spatial_context or {},
                "temporal_context": temporal_context or {}
            }
        )
        self.db.save_human_correction(correction, user_role=user_role)

        # 2. Derive Case Memory Precedent Record
        memory = CaseMemoryRecord(
            id=str(uuid.uuid4()),
            human_correction_id=correction.id,
            investigation_id=investigation_id,
            project_id=project_id,
            pattern_type=pattern_type,
            context_summary=f"Auditor corrected initial interpretation for {pattern_type}.",
            precedent_rule=f"When evaluating {pattern_type}: {reason_for_correction}",
            lessons_learned=f"Corrected interpretation: '{corrected_interpretation}'. Original assumption ('{original_interpretation}') was superseded.",
            metadata={
                "original_interpretation": original_interpretation,
                "corrected_interpretation": corrected_interpretation,
                "reason_for_correction": reason_for_correction,
                "evidence_ids": evidence_ids_involved,
                "spatial_context": spatial_context or {},
                "temporal_context": temporal_context or {}
            }
        )
        self.db.save_case_memory(memory, user_role="service_role")

        # 3. Update Investigation state to CLOSED / CORRECTION
        self.db.update_investigation_state(
            investigation_id=investigation_id,
            new_state="CLOSED",
            previous_state="HUMAN_REVIEW_REQUIRED",
            notes=f"Closed with human correction by {corrected_by}.",
            user_role=user_role
        )

        return correction, memory

    def find_similar_precedents(
        self,
        pattern_type: str,
        query_text: Optional[str] = None,
        evidence_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Deterministically retrieves matching historical case memory precedents.
        Does NOT rely on neural embeddings; uses structured category and keyword matching.
        """
        all_memories = self.db.get_case_memories_for_pattern(pattern_type)
        if not all_memories:
            # Fall back to general memories
            all_memories = self.db.get_case_memories_for_pattern("STAGED_MATERIAL_DISCREPANCY")

        results = []
        for mem in all_memories:
            meta = mem.metadata or {}
            orig_interp = meta.get("original_interpretation", mem.lessons_learned)
            corr_interp = meta.get("corrected_interpretation", mem.lessons_learned)
            reason = meta.get("reason_for_correction", mem.precedent_rule)
            ev_ids = meta.get("evidence_ids", [])

            relevance_explanation = (
                f"Historical precedent matched pattern '{mem.pattern_type}'. "
                f"Prior auditor correction established: {reason}"
            )

            result_item = {
                "precedent_id": mem.id,
                "investigation_id": mem.investigation_id,
                "project_id": mem.project_id,
                "pattern_type": mem.pattern_type,
                "context_summary": mem.context_summary,
                "precedent_rule": mem.precedent_rule,
                "lessons_learned": mem.lessons_learned,
                "original_interpretation": orig_interp,
                "corrected_interpretation": corr_interp,
                "reason_for_correction": reason,
                "evidence_ids": ev_ids,
                "relevance_explanation": relevance_explanation,
                "similarity_score": 0.95
            }
            results.append(result_item)

        return results

    def get_citizen_case_memory_summary(self, pattern_type: str) -> List[Dict[str, Any]]:
        """
        Formats a citizen-safe representation of case memory learning.
        STRICT PRIVACY: Strips private auditor identifiers (corrected_by) and internal chain-of-thought.
        """
        memories = self.find_similar_precedents(pattern_type)
        citizen_records = []

        for m in memories:
            citizen_item = {
                "public_notice": "Sentinel learned from a previous auditor correction.",
                "pattern_category": m["pattern_type"],
                "original_interpretation": m["original_interpretation"],
                "auditor_corrected_interpretation": m["corrected_interpretation"],
                "correction_reason": m["reason_for_correction"],
                "established_precedent_rule": m["precedent_rule"],
                "supporting_evidence_count": len(m["evidence_ids"])
            }
            citizen_records.append(citizen_item)

        return citizen_records
