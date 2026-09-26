"""
Evidence Intake Agent.
Classifies empirical evidence items, links them to claims, and identifies missing evidence gaps.
Supports Claude API integration with strict validation and evidence grounding.
"""
import os
from typing import List, Optional, Dict, Any, Set
from sentinel.agents.base import BaseAgent
from sentinel.types import AgentResult, Project, Claim, EvidenceItem, CaseMemoryRecord
from sentinel.claude_client import ClaudeClient


class EvidenceIntakeAgent(BaseAgent):
    PROMPT_VERSION = "intake_v1.txt"

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        self.claude_client = claude_client
        self._prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", self.PROMPT_VERSION)
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    @property
    def agent_name(self) -> str:
        return "Evidence Intake Agent"

    def execute(
        self,
        project: Project,
        claims: List[Claim],
        evidence_items: List[EvidenceItem],
        context_memories: List[CaseMemoryRecord] = None,
        investigation_id: str = "inv-unknown",
        db=None
    ) -> AgentResult:
        # Deterministic fallback calculation
        fallback_res = self._fallback_execute(project, claims, evidence_items)
        valid_ev_ids: Set[str] = {e.id for e in evidence_items}

        if not self.claude_client:
            return fallback_res

        # Construct prompt for Claude
        prompt_text = self._build_prompt(project, claims, evidence_items)

        # Invoke Claude via Client with strict validation
        result, _ = self.claude_client.invoke_agent_reasoning(
            investigation_id=investigation_id,
            agent_type=self.agent_name,
            prompt_version=self.PROMPT_VERSION,
            prompt_text=prompt_text,
            valid_evidence_ids=valid_ev_ids,
            fallback_result=fallback_res,
            db=db
        )
        return result

    def _build_prompt(self, project: Project, claims: List[Claim], evidence_items: List[EvidenceItem]) -> str:
        claims_summary = [f"- Claim ID: {c.id}, Type: {c.claim_type}, Desc: {c.description}, Value: {c.claimed_value} {c.unit}" for c in claims]
        evidence_summary = [
            f"- Evidence ID: {e.id}, Type: {e.source_type}, SourceID: {e.source_id}, Observation: {e.observation}, Value: {e.value} {e.unit}, Relationship: {e.relationship}, Reliability: {e.reliability}"
            for e in evidence_items
        ]
        return (
            f"{self._prompt_template}\n\n"
            f"PROJECT CONTEXT:\n- Code: {project.code}, Name: {project.name}, Sanctioned: ₹{project.sanctioned_amount:,.2f}, Released: ₹{project.released_amount:,.2f}\n\n"
            f"CLAIMS:\n" + "\n".join(claims_summary) + "\n\n"
            f"SUPPLIED EVIDENCE ITEMS:\n" + "\n".join(evidence_summary) + "\n\n"
            "Analyze the above evidence and respond ONLY with the required JSON object."
        )

    def _fallback_execute(self, project: Project, claims: List[Claim], evidence_items: List[EvidenceItem]) -> AgentResult:
        if not evidence_items:
            return AgentResult(
                agent_type=self.agent_name,
                finding="NO_EVIDENCE_FOUND",
                evidence_ids=[],
                confidence=1.0,
                severity="HIGH",
                reasoning_summary="No evidence records exist for the project. Severe evidentiary gap identified."
            )

        supported_ids = [e.id for e in evidence_items if e.relationship == "SUPPORTS"]
        contradictory_ids = [e.id for e in evidence_items if e.relationship == "CONTRADICTS"]
        insufficient_ids = [e.id for e in evidence_items if e.relationship == "INSUFFICIENT"]
        neutral_ids = [e.id for e in evidence_items if e.relationship == "NEUTRAL"]
        all_ids = [e.id for e in evidence_items]

        missing_bank_voucher = any(e.source_type == "BANK_STATEMENT" and e.relationship == "INSUFFICIENT" for e in evidence_items)

        summary_parts = [
            f"Processed {len(evidence_items)} empirical evidence items across project claims.",
            f"Found {len(supported_ids)} supporting, {len(contradictory_ids)} contradictory, {len(neutral_ids)} neutral, and {len(insufficient_ids)} insufficient evidence items."
        ]

        if missing_bank_voucher:
            summary_parts.append("Identified missing official bank clearance documentation for tranche disbursements.")

        severity = "HIGH" if contradictory_ids or missing_bank_voucher else ("MEDIUM" if insufficient_ids else "LOW")
        finding_code = "EVIDENCE_CONTRADICTION_DETECTED" if contradictory_ids else ("EVIDENTIARY_GAPS_IDENTIFIED" if insufficient_ids else "EVIDENCE_INTAKE_COMPLETE")

        return AgentResult(
            agent_type=self.agent_name,
            finding=finding_code,
            evidence_ids=all_ids,
            confidence=0.95,
            severity=severity,
            reasoning_summary=" ".join(summary_parts)
        )
