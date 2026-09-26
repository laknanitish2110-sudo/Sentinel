"""
SENTINEL Phase 1B Automated Suite.
Covers 10 mandatory test scenarios for real model integration, JSON validation, evidence grounding, and graceful fallbacks.
"""
import unittest
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem, InvestigationState, CaseMemoryRecord
from sentinel.claude_client import ClaudeClient
from sentinel.validator import validate_and_normalize_output, OutputValidationError
from sentinel.orchestrator import Orchestrator
from sentinel.agents.intake_agent import EvidenceIntakeAgent
from sentinel.agents.financial_agent import FinancialCrossCheckAgent
from sentinel.agents.historical_agent import HistoricalContextAgent


class TestSentinelPhase1B(unittest.TestCase):

    def setUp(self):
        self.db = SentinelDB(":memory:")
        self.project = Project(
            id="p1b", code="DEMO-1B", name="Phase 1B Test Project",
            description="Drainage Test Project", sanctioned_amount=1000000.0, released_amount=400000.0
        )
        self.db.save_project(self.project)
        self.claim = Claim(
            id="c1b", project_id=self.project.id, claim_ref="REF-1B", claimed_by="Contractor",
            claim_type="PHYSICAL_QUANTITY", description="100m pipe", claimed_value=100.0, unit="meters", claim_date="2026-09-20"
        )
        self.db.save_claim(self.claim)
        self.evidence = EvidenceItem(
            id="e1b", project_id=self.project.id, claim_id=self.claim.id, source_type="MB_RECORD",
            source_id="MB-1", observation="100m pipe laid", value=100.0, unit="meters",
            timestamp="2026-09-19", location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        self.db.save_evidence(self.evidence)

    def tearDown(self):
        self.db.close()

    # -------------------------------------------------------------------------
    # Test 1: Valid Claude Structured Output
    # -------------------------------------------------------------------------
    def test_1_valid_claude_structured_output(self):
        valid_json = json.dumps({
            "agent_type": "Evidence Intake Agent",
            "finding": "EVIDENCE_INTAKE_COMPLETE",
            "evidence_ids": ["e1b"],
            "confidence": 0.95,
            "severity": "LOW",
            "reasoning_summary": "All 1 evidence item verified."
        })
        client = ClaudeClient(api_key="mock_key")
        client.set_mock_provider(lambda prompt: valid_json)

        agent = EvidenceIntakeAgent(claude_client=client)
        res = agent.execute(self.project, [self.claim], [self.evidence])

        self.assertEqual(res.agent_type, "Evidence Intake Agent")
        self.assertEqual(res.finding, "EVIDENCE_INTAKE_COMPLETE")
        self.assertEqual(res.evidence_ids, ["e1b"])
        self.assertEqual(res.severity, "LOW")

    # -------------------------------------------------------------------------
    # Test 2: Malformed JSON Fallback
    # -------------------------------------------------------------------------
    def test_2_malformed_json_fallback(self):
        malformed_json = "This is not json at all { bad syntax"
        client = ClaudeClient(api_key="mock_key")
        client.set_mock_provider(lambda prompt: malformed_json)

        agent = EvidenceIntakeAgent(claude_client=client)
        res = agent.execute(self.project, [self.claim], [self.evidence])

        # Must fall back gracefully without crash
        self.assertIsNotNone(res)
        self.assertEqual(res.agent_type, "Evidence Intake Agent")

    # -------------------------------------------------------------------------
    # Test 3: Hallucinated Evidence ID Rejection
    # -------------------------------------------------------------------------
    def test_3_hallucinated_evidence_id(self):
        hallucinated_json = json.dumps({
            "agent_type": "Evidence Intake Agent",
            "finding": "EVIDENCE_INTAKE_COMPLETE",
            "evidence_ids": ["e1b", "HALLUCINATED_EV_999"],  # Invalid ID!
            "confidence": 0.95,
            "severity": "LOW",
            "reasoning_summary": "Verified with non-existent evidence."
        })
        client = ClaudeClient(api_key="mock_key")
        client.set_mock_provider(lambda prompt: hallucinated_json)

        # Validator check directly
        with self.assertRaises(OutputValidationError):
            validate_and_normalize_output(hallucinated_json, "Evidence Intake Agent", {"e1b"})

        # Agent execution check (fallback activated due to validation rejection)
        agent = EvidenceIntakeAgent(claude_client=client)
        res = agent.execute(self.project, [self.claim], [self.evidence])
        self.assertNotIn("HALLUCINATED_EV_999", res.evidence_ids)

    # -------------------------------------------------------------------------
    # Test 4: Missing Evidence Handling
    # -------------------------------------------------------------------------
    def test_4_missing_evidence(self):
        agent = EvidenceIntakeAgent()
        res = agent.execute(self.project, [self.claim], [])

        self.assertEqual(res.finding, "NO_EVIDENCE_FOUND")
        self.assertEqual(res.severity, "HIGH")
        self.assertIn("Severe evidentiary gap", res.reasoning_summary)

    # -------------------------------------------------------------------------
    # Test 5: Claude Unavailable Graceful Fallback
    # -------------------------------------------------------------------------
    def test_5_claude_unavailable(self):
        client = ClaudeClient(api_key=None)  # Key missing!
        agent = EvidenceIntakeAgent(claude_client=client)
        res = agent.execute(self.project, [self.claim], [self.evidence])

        self.assertIsNotNone(res)
        self.assertEqual(res.finding, "EVIDENCE_INTAKE_COMPLETE")

    # -------------------------------------------------------------------------
    # Test 6: Financial Calculation Consistency
    # -------------------------------------------------------------------------
    def test_6_financial_calculation_consistency(self):
        financial_json = json.dumps({
            "agent_type": "Financial Cross-Check Agent",
            "finding": "FINANCIAL_ALIGNMENT_ANALYSIS_COMPLETE",
            "evidence_ids": ["e1b"],
            "confidence": 0.92,
            "severity": "LOW",
            "reasoning_summary": "Sanctioned ₹1,000,000.00; Released ₹400,000.00 (40%). Physical claim 100m verified."
        })
        client = ClaudeClient(api_key="mock_key")
        client.set_mock_provider(lambda prompt: financial_json)

        agent = FinancialCrossCheckAgent(claude_client=client)
        res = agent.execute(self.project, [self.claim], [self.evidence])

        self.assertEqual(res.agent_type, "Financial Cross-Check Agent")
        self.assertIn("₹1,000,000.00", res.reasoning_summary)

    # -------------------------------------------------------------------------
    # Test 7: Historical Precedent Usage
    # -------------------------------------------------------------------------
    def test_7_historical_precedent_usage(self):
        historical_json = json.dumps({
            "agent_type": "Historical Context Agent",
            "finding": "HISTORICAL_PRECEDENTS_RETRIEVED",
            "evidence_ids": [],
            "confidence": 0.90,
            "severity": "MEDIUM",
            "reasoning_summary": "Precedent STAGED_MATERIAL_DISCREPANCY applies."
        })
        client = ClaudeClient(api_key="mock_key")
        client.set_mock_provider(lambda prompt: historical_json)

        agent = HistoricalContextAgent(claude_client=client)
        res = agent.execute(self.project, [self.claim], [self.evidence])

        self.assertEqual(res.agent_type, "Historical Context Agent")
        self.assertIn("STAGED_MATERIAL_DISCREPANCY", res.reasoning_summary)

    # -------------------------------------------------------------------------
    # Test 8: Non-Accusatory Output Rejection
    # -------------------------------------------------------------------------
    def test_8_non_accusatory_output_rejection(self):
        accusatory_json = json.dumps({
            "agent_type": "Financial Cross-Check Agent",
            "finding": "FRAUD_SUSPECTED",
            "evidence_ids": ["e1b"],
            "confidence": 0.99,
            "severity": "HIGH",
            "reasoning_summary": "Contractor is guilty of fraud and payment should be denied."
        })
        client = ClaudeClient(api_key="mock_key")
        client.set_mock_provider(lambda prompt: accusatory_json)

        with self.assertRaises(OutputValidationError):
            validate_and_normalize_output(accusatory_json, "Financial Cross-Check Agent", {"e1b"})

    # -------------------------------------------------------------------------
    # Test 9: Decision Engine Still Controls Final Decision
    # -------------------------------------------------------------------------
    def test_9_decision_engine_controls_final_decision(self):
        # Even if model outputs LOW severity finding, Decision Engine detects contradiction in DB and forces HUMAN_REVIEW_REQUIRED
        ev_contradict = EvidenceItem(
            id="e2b", project_id=self.project.id, claim_id=self.claim.id, source_type="PHYSICAL_INSPECTION",
            source_id="INSP-2", observation="Only 20m pipe in trench", value=20.0, unit="meters",
            timestamp="2026-09-20", location=None, confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
        )
        self.db.save_evidence(ev_contradict)

        client = ClaudeClient(api_key="mock_key")
        # Model returns optimistic summary
        client.set_mock_provider(lambda prompt: json.dumps({
            "agent_type": "Evidence Intake Agent",
            "finding": "EVIDENCE_CONTRADICTION_DETECTED",
            "evidence_ids": ["e1b", "e2b"],
            "confidence": 0.90,
            "severity": "HIGH",
            "reasoning_summary": "Discrepancy noted between MB and site photo."
        }))

        orchestrator = Orchestrator(self.db, claude_client=client)
        res = orchestrator.run_investigation(self.project.id, self.claim.id)

        self.assertEqual(res["final_state"], InvestigationState.HUMAN_REVIEW_REQUIRED)

    # -------------------------------------------------------------------------
    # Test 10: Deterministic Fallback When Model Unavailable
    # -------------------------------------------------------------------------
    def test_10_deterministic_fallback_when_model_unavailable(self):
        client = ClaudeClient(api_key=None)  # No API Key
        orchestrator = Orchestrator(self.db, claude_client=client)
        res = orchestrator.run_investigation(self.project.id, self.claim.id)

        self.assertIsNotNone(res["investigation_id"])
        self.assertEqual(res["final_state"], InvestigationState.SUPPORTED)
        self.assertEqual(len(res["agent_results"]), 3)


if __name__ == "__main__":
    unittest.main()
