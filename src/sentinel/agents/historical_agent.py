"""
Historical Context Agent.
Retrieves past human auditor corrections and structured case memory precedents to inform current investigation context.
Supports Claude API integration with strict validation and evidence grounding.
"""
import os
from typing import List, Optional, Dict, Any, Set
from sentinel.agents.base import BaseAgent
from sentinel.types import AgentResult, Project, Claim, EvidenceItem, CaseMemoryRecord
from sentinel.claude_client import ClaudeClient


class HistoricalContextAgent(BaseAgent):
    PROMPT_VERSION = "historical_v1.txt"

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
        return "Historical Context Agent"

    def execute(
        self,
        project: Project,
        claims: List[Claim],
        evidence_items: List[EvidenceItem],
        context_memories: List[CaseMemoryRecord] = None,
        investigation_id: str = "inv-unknown",
        db=None
    ) -> AgentResult:
        fallback_res = self._fallback_execute(project, claims, evidence_items, context_memories)
        valid_ev_ids: Set[str] = {e.id for e in evidence_items}

        if not self.claude_client:
            return fallback_res

        prompt_text = self._build_prompt(project, claims, evidence_items, context_memories)

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

    def _build_prompt(self, project: Project, claims: List[Claim], evidence_items: List[EvidenceItem], context_memories: Optional[List[CaseMemoryRecord]]) -> str:
        memories = context_memories or []
        mem_summary = [f"- Pattern: {m.pattern_type}, Rule: {m.precedent_rule}, Lessons: {m.lessons_learned}" for m in memories]

        return (
            f"{self._prompt_template}\n\n"
            f"PROJECT: {project.name} ({project.code})\n\n"
            f"RETRIEVED PRECEDENT MEMORIES:\n" + ("\n".join(mem_summary) if mem_summary else "None found.") + "\n\n"
            "Analyze historical precedent and respond ONLY with the required JSON object."
        )

    def _fallback_execute(self, project: Project, claims: List[Claim], evidence_items: List[EvidenceItem], context_memories: Optional[List[CaseMemoryRecord]]) -> AgentResult:
        memories = context_memories or []
        if not memories:
            return AgentResult(
                agent_type=self.agent_name,
                finding="NO_HISTORICAL_PRECEDENTS_FOUND",
                evidence_ids=[],
                confidence=0.85,
                severity="LOW",
                reasoning_summary="No prior human corrections or precedent case memories matched the current project context."
            )

        precedent_summaries = []
        for mem in memories:
            precedent_summaries.append(
                f"[Precedent {mem.pattern_type}]: {mem.precedent_rule} (Lesson: {mem.lessons_learned})"
            )

        summary_text = (
            f"Retrieved {len(memories)} relevant historical case memory precedent(s). "
            + " ".join(precedent_summaries)
        )

        return AgentResult(
            agent_type=self.agent_name,
            finding="HISTORICAL_PRECEDENTS_RETRIEVED",
            evidence_ids=[],
            confidence=0.95,
            severity="MEDIUM",
            reasoning_summary=summary_text
        )
