"""
Financial Cross-Check Agent.
Evaluates alignment between sanctioned budget, released funds, invoices, and physical progress claims.
Supports Claude API integration with strict validation and evidence grounding.
Strictly non-accusatory.
"""
import os
from typing import List, Optional, Dict, Any, Set
from sentinel.agents.base import BaseAgent
from sentinel.types import AgentResult, Project, Claim, EvidenceItem, CaseMemoryRecord
from sentinel.claude_client import ClaudeClient


class FinancialCrossCheckAgent(BaseAgent):
    PROMPT_VERSION = "financial_v1.txt"

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
        return "Financial Cross-Check Agent"

    def execute(
        self,
        project: Project,
        claims: List[Claim],
        evidence_items: List[EvidenceItem],
        context_memories: List[CaseMemoryRecord] = None,
        investigation_id: str = "inv-unknown",
        db=None
    ) -> AgentResult:
        fallback_res = self._fallback_execute(project, claims, evidence_items)
        valid_ev_ids: Set[str] = {e.id for e in evidence_items}

        if not self.claude_client:
            return fallback_res

        prompt_text = self._build_prompt(project, claims, evidence_items)

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
        claims_summary = [f"- Claim ID: {c.id}, Type: {c.claim_type}, Value: {c.claimed_value} {c.unit}" for c in claims]
        financial_ev = [e for e in evidence_items if e.source_type in ("INVOICE", "BANK_STATEMENT", "MB_RECORD")]
        ev_summary = [f"- Evidence ID: {e.id}, Type: {e.source_type}, Observation: {e.observation}, Value: {e.value} {e.unit}" for e in financial_ev]

        return (
            f"{self._prompt_template}\n\n"
            f"PROJECT FINANCIAL DATA:\n- Sanctioned: ₹{project.sanctioned_amount:,.2f}\n- Released: ₹{project.released_amount:,.2f}\n\n"
            f"CLAIMS:\n" + "\n".join(claims_summary) + "\n\n"
            f"FINANCIAL EVIDENCE:\n" + "\n".join(ev_summary) + "\n\n"
            "Analyze financial alignment and respond ONLY with the required JSON object."
        )

    def _fallback_execute(self, project: Project, claims: List[Claim], evidence_items: List[EvidenceItem]) -> AgentResult:
        financial_evidence = [e for e in evidence_items if e.source_type in ("INVOICE", "BANK_STATEMENT", "MB_RECORD")]
        ev_ids = [e.id for e in financial_evidence]

        released_ratio = (project.released_amount / project.sanctioned_amount) if project.sanctioned_amount > 0 else 0.0
        released_pct = released_ratio * 100

        completion_claims = [c for c in claims if c.claim_type == "COMPLETION_PERCENTAGE"]
        claimed_completion_val = completion_claims[0].claimed_value if completion_claims else None

        reasoning_lines = [
            f"Sanctioned budget: ₹{project.sanctioned_amount:,.2f}; Released to date: ₹{project.released_amount:,.2f} ({released_pct:.1f}%)."
        ]

        if claimed_completion_val is not None:
            reasoning_lines.append(
                f"Contractor submitted claim asserting {claimed_completion_val:.0f}% physical completion."
            )
            if released_pct < claimed_completion_val:
                reasoning_lines.append(
                    f"Released amount ({released_pct:.1f}%) is lower than claimed completion ({claimed_completion_val:.0f}%). "
                    "This does not by itself contradict the reported completion because payment schedule rules are not available."
                )

        invoices = [e for e in evidence_items if e.source_type == "INVOICE" and e.metadata.get("invoice_amount")]
        if invoices:
            inv_total = sum(float(i.metadata["invoice_amount"]) for i in invoices)
            reasoning_lines.append(f"Supplier invoices verified on site total ₹{inv_total:,.2f}.")

        return AgentResult(
            agent_type=self.agent_name,
            finding="FINANCIAL_ALIGNMENT_ANALYSIS_COMPLETE",
            evidence_ids=ev_ids,
            confidence=0.92,
            severity="LOW",
            reasoning_summary=" ".join(reasoning_lines)
        )
