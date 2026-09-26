"""
Sentinel Investigation Orchestrator.
Manages deterministic investigation state machine transitions, agent invocations, and database persistence.
Supports optional Claude API client integration.
"""
from typing import List, Dict, Any, Optional
from sentinel.db import SentinelDB
from sentinel.types import (
    Project, Claim, EvidenceItem, AgentResult, Finding, ContradictionRecord,
    InvestigationState, CaseMemoryRecord
)
from sentinel.claude_client import ClaudeClient
from sentinel.agents.intake_agent import EvidenceIntakeAgent
from sentinel.agents.financial_agent import FinancialCrossCheckAgent
from sentinel.agents.historical_agent import HistoricalContextAgent
from sentinel.engines.contradiction_engine import ContradictionEngine
from sentinel.engines.decision_engine import DecisionEngine


# Valid State Transitions Graph
VALID_TRANSITIONS = {
    InvestigationState.CREATED: [InvestigationState.INTAKE],
    InvestigationState.INTAKE: [InvestigationState.CLAIMS_IDENTIFIED],
    InvestigationState.CLAIMS_IDENTIFIED: [InvestigationState.EVIDENCE_COLLECTION],
    InvestigationState.EVIDENCE_COLLECTION: [InvestigationState.CROSS_CHECK],
    InvestigationState.CROSS_CHECK: [InvestigationState.CONFLICT_ANALYSIS],
    InvestigationState.CONFLICT_ANALYSIS: [InvestigationState.DECISION],
    InvestigationState.DECISION: [
        InvestigationState.SUPPORTED,
        InvestigationState.PARTIALLY_SUPPORTED,
        InvestigationState.CONTRADICTED,
        InvestigationState.INSUFFICIENT_EVIDENCE,
        InvestigationState.HUMAN_REVIEW_REQUIRED
    ],
    InvestigationState.HUMAN_REVIEW_REQUIRED: [InvestigationState.CORRECTION, InvestigationState.CLOSED],
    InvestigationState.CORRECTION: [InvestigationState.CASE_MEMORY],
    InvestigationState.CASE_MEMORY: [InvestigationState.CLOSED],
    InvestigationState.CLOSED: []
}


class Orchestrator:
    def __init__(self, db: SentinelDB, claude_client: Optional[ClaudeClient] = None):
        self.db = db
        self.claude_client = claude_client
        self.intake_agent = EvidenceIntakeAgent(claude_client=claude_client)
        self.financial_agent = FinancialCrossCheckAgent(claude_client=claude_client)
        self.historical_agent = HistoricalContextAgent(claude_client=claude_client)
        self.contradiction_engine = ContradictionEngine(db=db)
        self.decision_engine = DecisionEngine()

    def validate_transition(self, current_state: str, target_state: str):
        allowed = VALID_TRANSITIONS.get(current_state, [])
        if target_state not in allowed:
            raise ValueError(
                f"Invalid investigation state transition from '{current_state}' to '{target_state}'. "
                f"Allowed transitions: {allowed}"
            )

    def run_investigation(
        self,
        project_id: str,
        claim_id: Optional[str] = None,
        user_role: str = "service_role"
    ) -> Dict[str, Any]:
        """Runs an end-to-end investigation vertical slice for a project/claim."""
        project = self.db.get_project(project_id)
        if not project:
            raise ValueError(f"Project with ID '{project_id}' not found.")

        all_claims = self.db.get_claims_for_project(project_id)
        if claim_id:
            target_claims = [c for c in all_claims if c.id == claim_id]
        else:
            target_claims = all_claims

        all_evidence = self.db.get_evidence_for_project(project_id)
        if claim_id:
            target_evidence = [e for e in all_evidence if e.claim_id == claim_id or e.claim_id is None]
        else:
            target_evidence = all_evidence

        # 1. CREATED
        investigation_id = self.db.create_investigation(
            project_id=project_id,
            title=f"Investigation for Project {project.code} ({project.name})",
            user_role=user_role
        )
        current_state = InvestigationState.CREATED

        # 2. INTAKE
        self.validate_transition(current_state, InvestigationState.INTAKE)
        self.db.update_investigation_state(investigation_id, InvestigationState.INTAKE, current_state, user_role=user_role)
        current_state = InvestigationState.INTAKE
        intake_res = self.intake_agent.execute(
            project, target_claims, target_evidence, investigation_id=investigation_id, db=self.db
        )
        self._persist_agent_finding(investigation_id, project_id, claim_id, intake_res, user_role=user_role)

        # 3. CLAIMS_IDENTIFIED
        self.validate_transition(current_state, InvestigationState.CLAIMS_IDENTIFIED)
        self.db.update_investigation_state(investigation_id, InvestigationState.CLAIMS_IDENTIFIED, current_state, user_role=user_role)
        current_state = InvestigationState.CLAIMS_IDENTIFIED

        # 4. EVIDENCE_COLLECTION
        self.validate_transition(current_state, InvestigationState.EVIDENCE_COLLECTION)
        self.db.update_investigation_state(investigation_id, InvestigationState.EVIDENCE_COLLECTION, current_state, user_role=user_role)
        current_state = InvestigationState.EVIDENCE_COLLECTION

        # 5. CROSS_CHECK
        self.validate_transition(current_state, InvestigationState.CROSS_CHECK)
        self.db.update_investigation_state(investigation_id, InvestigationState.CROSS_CHECK, current_state, user_role=user_role)
        current_state = InvestigationState.CROSS_CHECK
        financial_res = self.financial_agent.execute(
            project, target_claims, target_evidence, investigation_id=investigation_id, db=self.db
        )
        self._persist_agent_finding(investigation_id, project_id, claim_id, financial_res, user_role=user_role)

        # 6. CONFLICT_ANALYSIS & HISTORICAL LOOKUP
        self.validate_transition(current_state, InvestigationState.CONFLICT_ANALYSIS)
        self.db.update_investigation_state(investigation_id, InvestigationState.CONFLICT_ANALYSIS, current_state, user_role=user_role)
        current_state = InvestigationState.CONFLICT_ANALYSIS

        # Check for precedents
        context_memories = self.db.get_case_memories_for_pattern("STAGED_MATERIAL_DISCREPANCY")
        historical_res = self.historical_agent.execute(
            project, target_claims, target_evidence, context_memories, investigation_id=investigation_id, db=self.db
        )

        # Generate structured contradictions
        contradictions = self.contradiction_engine.evaluate_contradictions(
            investigation_id=investigation_id,
            project_id=project_id,
            claim_id=claim_id,
            evidence_items=target_evidence
        )
        for con in contradictions:
            self.db.save_contradiction(con, user_role=user_role)

        # 7. DECISION
        self.validate_transition(current_state, InvestigationState.DECISION)
        self.db.update_investigation_state(investigation_id, InvestigationState.DECISION, current_state, user_role=user_role)
        current_state = InvestigationState.DECISION

        agent_results = [intake_res, financial_res, historical_res]
        final_state, decision_notes = self.decision_engine.evaluate_decision(
            agent_results=agent_results,
            contradictions=contradictions,
            evidence_items=target_evidence,
            case_memories=context_memories
        )

        self.validate_transition(current_state, final_state)
        self.db.update_investigation_state(investigation_id, final_state, current_state, notes=decision_notes, user_role=user_role)

        return {
            "investigation_id": investigation_id,
            "project_id": project_id,
            "final_state": final_state,
            "decision_notes": decision_notes,
            "agent_results": [r.to_dict() for r in agent_results],
            "contradiction_count": len(contradictions),
            "events": self.db.get_investigation_events(investigation_id)
        }

    def _persist_agent_finding(self, investigation_id: str, project_id: str, claim_id: Optional[str], result: AgentResult, user_role: str = "service_role"):
        import uuid
        finding = Finding(
            id=str(uuid.uuid4()),
            investigation_id=investigation_id,
            project_id=project_id,
            claim_id=claim_id,
            agent_name=result.agent_type,
            finding_type=result.finding,
            summary=result.reasoning_summary,
            reasoning=result.reasoning_summary,
            confidence=result.confidence,
            evidence_ids=result.evidence_ids
        )
        self.db.save_finding(finding, user_role=user_role)
        self.db.record_event(investigation_id, "AGENT_EXECUTION", agent_name=result.agent_type, details=result.to_dict())
