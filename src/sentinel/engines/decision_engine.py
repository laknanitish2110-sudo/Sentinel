"""
Decision Engine.
Evaluates agent findings, evidence graph, contradictions, and precedent memory to render a deterministic investigation state.
Enforces uncertainty and human review invariants.
"""
from typing import List, Dict, Any, Tuple
from sentinel.types import (
    AgentResult, ContradictionRecord, EvidenceItem, CaseMemoryRecord, InvestigationState
)


class DecisionEngine:
    def evaluate_decision(
        self,
        agent_results: List[AgentResult],
        contradictions: List[ContradictionRecord],
        evidence_items: List[EvidenceItem],
        case_memories: List[CaseMemoryRecord]
    ) -> Tuple[InvestigationState, str]:
        """
        Evaluates accumulated inputs and returns (FinalState, DecisionNotes).
        DECISION PRIORITY:
        1. Material / High Severity Contradiction Check (Explicit record or SUPPORTS + CONTRADICTS evidence pair)
           -> Escalates to HUMAN_REVIEW_REQUIRED (or PARTIALLY_SUPPORTED if historical precedent applies)
        2. Missing / Insufficient Evidence Check (Returns INSUFFICIENT_EVIDENCE if no material contradiction exists)
        3. Single Contradiction check
        4. Full Support check
        """
        # Rule 1: High severity contradiction check (Material contradiction takes priority over insufficient evidence)
        has_high_severity_record = any(c.severity in ("HIGH", "CRITICAL") for c in contradictions)
        has_conflicting_pair = any(e.relationship == "SUPPORTS" for e in evidence_items) and any(e.relationship == "CONTRADICTS" for e in evidence_items)

        if has_high_severity_record or has_conflicting_pair:
            # Check if historical case memory offers a precedent rule explaining this discrepancy
            relevant_precedents = [m for m in case_memories if m.pattern_type in ("STAGED_MATERIAL_DISCREPANCY", "PARTIAL_PAYMENT_TIMING")]
            if relevant_precedents:
                rule_text = relevant_precedents[0].precedent_rule
                notes = (
                    f"Discrepancy detected between site photo and MB record. However, historical case memory precedent "
                    f"[{relevant_precedents[0].pattern_type}] applies: '{rule_text}'. Claim evaluated as PARTIALLY_SUPPORTED."
                )
                return InvestigationState.PARTIALLY_SUPPORTED, notes

            # No historical precedent to resolve conflict -> mandatory human review escalation
            notes = (
                f"Unresolved contradiction detected between physical site inspection and government MB entry. "
                "Escalating to HUMAN_REVIEW_REQUIRED. Human auditor review is mandated."
            )
            return InvestigationState.HUMAN_REVIEW_REQUIRED, notes

        # Rule 2: Missing / Insufficient evidence check (Genuinely insufficient-only cases without material contradiction)
        insufficient_ev = [e for e in evidence_items if e.relationship == "INSUFFICIENT"]
        if not evidence_items or len(insufficient_ev) > 0:
            notes = "Critical evidence is missing or unverified (e.g. missing bank clearance vouchers). Decision: INSUFFICIENT_EVIDENCE."
            return InvestigationState.INSUFFICIENT_EVIDENCE, notes

        # Rule 3: Contradictory evidence present without supporting pair or high severity conflict
        contradicting_ev = [e for e in evidence_items if e.relationship == "CONTRADICTS"]
        if contradicting_ev:
            notes = "Empirical site evidence directly refutes physical quantity claim without ambiguity. Decision: CONTRADICTED."
            return InvestigationState.CONTRADICTED, notes

        # Rule 4: Fully supported
        supporting_ev = [e for e in evidence_items if e.relationship == "SUPPORTS"]
        if supporting_ev and len(supporting_ev) == len([e for e in evidence_items if e.relationship != "NEUTRAL"]):
            notes = "All contractor claims corroborated by high-reliability empirical evidence. Decision: SUPPORTED."
            return InvestigationState.SUPPORTED, notes

        notes = "Evidence is partially verifying claims. Decision: PARTIALLY_SUPPORTED."
        return InvestigationState.PARTIALLY_SUPPORTED, notes
