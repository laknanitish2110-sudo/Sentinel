"""
Base Agent Interface for Sentinel MVP Agents.
Enforces the mandatory Agent Output Contract.
"""
from abc import ABC, abstractmethod
from typing import List
from sentinel.types import AgentResult, Project, Claim, EvidenceItem, CaseMemoryRecord


class BaseAgent(ABC):
    @property
    @abstractmethod
    def agent_name(self) -> str:
        pass

    @abstractmethod
    def execute(self, project: Project, claims: List[Claim], evidence_items: List[EvidenceItem], context_memories: List[CaseMemoryRecord] = None) -> AgentResult:
        """Executes agent analysis and returns a structured AgentResult conforming strictly to contract."""
        pass
