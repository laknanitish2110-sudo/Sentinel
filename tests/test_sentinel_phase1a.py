"""
SENTINEL Phase 1A Automated Suite.
Covers 10 mandatory test scenarios specified in Phase 1A requirements.
"""
import unittest
import uuid
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinel.db import SentinelDB, UnauthorizedWriteError
from sentinel.types import (
    Project, Claim, EvidenceItem, HumanCorrection, CaseMemoryRecord,
    InvestigationState, ContradictionRecord
)
from sentinel.orchestrator import Orchestrator
from sentinel.engines.case_memory_engine import CaseMemoryEngine
from sentinel.engines.contradiction_engine import ContradictionEngine


class TestSentinelPhase1A(unittest.TestCase):

    def setUp(self):
        self.db = SentinelDB(":memory:")

    def tearDown(self):
        self.db.close()

    def _setup_base_project(self, project_id="p1"):
        p = Project(
            id=project_id,
            code="DEMO-WARD7-DRAIN-2026",
            name="Ward 7 Drainage Improvement [DEMO DATA]",
            description="Construction of RCC storm water drain.",
            sanctioned_amount=1800000.0,
            released_amount=720000.0
        )
        self.db.save_project(p)
        return p

    # -------------------------------------------------------------------------
    # Test 1: Supported Scenario
    # -------------------------------------------------------------------------
    def test_1_supported_scenario(self):
        p = self._setup_base_project("p1")
        c = Claim(
            id="c1", project_id=p.id, claim_ref="CLAIM-1", claimed_by="Apex Infra",
            claim_type="PHYSICAL_QUANTITY", description="400m pipe installation",
            claimed_value=400.0, unit="meters", claim_date="2026-09-15"
        )
        self.db.save_claim(c)

        ev1 = EvidenceItem(
            id="e1", project_id=p.id, claim_id=c.id, source_type="MB_RECORD", source_id="MB-402",
            observation="JE cert 400m pipe", value=400.0, unit="meters", timestamp="2026-09-14",
            location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        ev2 = EvidenceItem(
            id="e2", project_id=p.id, claim_id=c.id, source_type="PHYSICAL_INSPECTION", source_id="INSP-001",
            observation="Photo verified 400m pipe in trench", value=400.0, unit="meters", timestamp="2026-09-15",
            location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        self.db.save_evidence(ev1)
        self.db.save_evidence(ev2)

        orchestrator = Orchestrator(self.db)
        res = orchestrator.run_investigation(project_id=p.id, claim_id=c.id)

        self.assertEqual(res["final_state"], InvestigationState.SUPPORTED)
        self.assertIn("SUPPORTED", res["decision_notes"])

    # -------------------------------------------------------------------------
    # Test 2: Contradiction Scenario
    # -------------------------------------------------------------------------
    def test_2_contradiction_scenario(self):
        p = self._setup_base_project("p2")
        c = Claim(
            id="c2", project_id=p.id, claim_ref="CLAIM-2", claimed_by="Apex Infra",
            claim_type="PHYSICAL_QUANTITY", description="400m pipe installation",
            claimed_value=400.0, unit="meters", claim_date="2026-09-15"
        )
        self.db.save_claim(c)

        ev1 = EvidenceItem(
            id="e1", project_id=p.id, claim_id=c.id, source_type="MB_RECORD", source_id="MB-402",
            observation="JE cert 400m pipe", value=400.0, unit="meters", timestamp="2026-09-14",
            location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        ev2 = EvidenceItem(
            id="e2", project_id=p.id, claim_id=c.id, source_type="PHYSICAL_INSPECTION", source_id="INSP-002",
            observation="Photo verified only 180m pipe in trench", value=180.0, unit="meters", timestamp="2026-09-15",
            location=None, confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
        )
        self.db.save_evidence(ev1)
        self.db.save_evidence(ev2)

        orchestrator = Orchestrator(self.db)
        res = orchestrator.run_investigation(project_id=p.id, claim_id=c.id)

        self.assertEqual(res["final_state"], InvestigationState.HUMAN_REVIEW_REQUIRED)
        self.assertNotIn("FRAUD", res["decision_notes"])
        self.assertGreaterEqual(res["contradiction_count"], 1)

    # -------------------------------------------------------------------------
    # Test 3: Insufficient Evidence Scenario
    # -------------------------------------------------------------------------
    def test_3_insufficient_evidence_scenario(self):
        p = self._setup_base_project("p3")
        c = Claim(
            id="c3", project_id=p.id, claim_ref="CLAIM-3", claimed_by="Apex Infra",
            claim_type="COMPLETION_PERCENTAGE", description="80% completion claim",
            claimed_value=80.0, unit="percent", claim_date="2026-09-15"
        )
        self.db.save_claim(c)

        ev1 = EvidenceItem(
            id="e1", project_id=p.id, claim_id=c.id, source_type="BANK_STATEMENT", source_id="TREASURY-01",
            observation="Missing official bank voucher", value=None, unit=None, timestamp="2026-09-14",
            location=None, confidence=0.50, reliability="UNVERIFIED", relationship="INSUFFICIENT"
        )
        self.db.save_evidence(ev1)

        orchestrator = Orchestrator(self.db)
        res = orchestrator.run_investigation(project_id=p.id, claim_id=c.id)

        self.assertEqual(res["final_state"], InvestigationState.INSUFFICIENT_EVIDENCE)

    # -------------------------------------------------------------------------
    # Test 4: Financial Inconsistency Non-Accusatory Test
    # -------------------------------------------------------------------------
    def test_4_financial_inconsistency_non_accusatory(self):
        p = self._setup_base_project("p4")
        c = Claim(
            id="c4", project_id=p.id, claim_ref="CLAIM-4", claimed_by="Apex Infra",
            claim_type="COMPLETION_PERCENTAGE", description="80% completion claim",
            claimed_value=80.0, unit="percent", claim_date="2026-09-15"
        )
        self.db.save_claim(c)

        orchestrator = Orchestrator(self.db)
        res = orchestrator.run_investigation(project_id=p.id, claim_id=c.id)

        fin_finding = [r for r in res["agent_results"] if r["agent_type"] == "Financial Cross-Check Agent"][0]
        self.assertNotIn("fraud", fin_finding["reasoning_summary"].lower())
        self.assertIn("does not by itself contradict", fin_finding["reasoning_summary"])

    # -------------------------------------------------------------------------
    # Test 5: Historical Precedent Retrieval Test
    # -------------------------------------------------------------------------
    def test_5_historical_precedent_retrieval(self):
        p = self._setup_base_project("p5")
        inv_id = self.db.create_investigation(p.id, "Inv 5", user_role="service_role")
        hc = HumanCorrection(
            id="hc1", investigation_id=inv_id, project_id=p.id, claim_id=None,
            corrected_by="Auditor Sharma", original_interpretation="Unexecuted work",
            corrected_interpretation="Staged material on site",
            reason_for_correction="Remaining pipes staged adjacent to trench in yard",
            evidence_ids_involved=[]
        )
        self.db.save_human_correction(hc, user_role="auditor")

        cm = CaseMemoryRecord(
            id="cm1", human_correction_id=hc.id, investigation_id=inv_id, project_id=p.id,
            pattern_type="STAGED_MATERIAL_DISCREPANCY",
            context_summary="Pipe trench photo discrepancy",
            precedent_rule="Check invoices for material delivery to site yard before flagging unexecuted work.",
            lessons_learned="Photos omit staging yard."
        )
        self.db.save_case_memory(cm, user_role="service_role")

        retrieved = self.db.get_case_memories_for_pattern("STAGED_MATERIAL_DISCREPANCY")
        self.assertEqual(len(retrieved), 1)
        self.assertIn("Check invoices", retrieved[0].precedent_rule)

    # -------------------------------------------------------------------------
    # Test 6: Human Correction Persistence Test
    # -------------------------------------------------------------------------
    def test_6_human_correction_persistence(self):
        p = self._setup_base_project("p6")
        inv_id = self.db.create_investigation(p.id, "Inv 6", user_role="service_role")

        cm_engine = CaseMemoryEngine(self.db)
        corr, mem = cm_engine.process_human_correction(
            investigation_id=inv_id,
            project_id=p.id,
            claim_id=None,
            corrected_by="Auditor K. Sharma",
            original_interpretation="Flagged unexecuted work",
            corrected_interpretation="Material staged on site",
            reason_for_correction="Pipes were in adjacent yard",
            evidence_ids_involved=[],
            pattern_type="STAGED_MATERIAL_DISCREPANCY",
            user_role="auditor"
        )

        self.assertIsNotNone(corr.id)
        self.assertIsNotNone(mem.id)

    # -------------------------------------------------------------------------
    # Test 7: Case Memory Retrieval in Next Investigation
    # -------------------------------------------------------------------------
    def test_7_case_memory_retrieval_in_next_investigation(self):
        p = self._setup_base_project("p7")
        c = Claim(
            id="c7", project_id=p.id, claim_ref="CLAIM-7", claimed_by="Apex Infra",
            claim_type="PHYSICAL_QUANTITY", description="400m pipe installation",
            claimed_value=400.0, unit="meters", claim_date="2026-09-15"
        )
        self.db.save_claim(c)

        ev1 = EvidenceItem(
            id="e1", project_id=p.id, claim_id=c.id, source_type="MB_RECORD", source_id="MB-402",
            observation="JE cert 400m pipe", value=400.0, unit="meters", timestamp="2026-09-14",
            location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        ev2 = EvidenceItem(
            id="e2", project_id=p.id, claim_id=c.id, source_type="PHYSICAL_INSPECTION", source_id="INSP-002",
            observation="Photo verified 180m pipe in trench", value=180.0, unit="meters", timestamp="2026-09-15",
            location=None, confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
        )
        self.db.save_evidence(ev1)
        self.db.save_evidence(ev2)

        # Pre-seed case memory precedent
        prior_inv_id = self.db.create_investigation(p.id, "Prior Inv", user_role="service_role")
        hc = HumanCorrection(
            id="hc7", investigation_id=prior_inv_id, project_id=p.id, claim_id=c.id,
            corrected_by="Auditor", original_interpretation="Unexecuted work",
            corrected_interpretation="Staged material", reason_for_correction="Material staged in yard",
            evidence_ids_involved=[ev1.id, ev2.id]
        )
        self.db.save_human_correction(hc, user_role="auditor")

        cm = CaseMemoryRecord(
            id="cm7", human_correction_id=hc.id, investigation_id=prior_inv_id, project_id=p.id,
            pattern_type="STAGED_MATERIAL_DISCREPANCY",
            context_summary="Trench photo omits staging yard",
            precedent_rule="Material delivered to site yard accounts for unlaid pipes.",
            lessons_learned="Check staging yard."
        )
        self.db.save_case_memory(cm, user_role="service_role")

        # Next investigation
        orchestrator = Orchestrator(self.db)
        res = orchestrator.run_investigation(project_id=p.id, claim_id=c.id)

        # The precedent applies, avoiding raw error state
        self.assertEqual(res["final_state"], InvestigationState.PARTIALLY_SUPPORTED)
        self.assertIn("STAGED_MATERIAL_DISCREPANCY", res["decision_notes"])

    # -------------------------------------------------------------------------
    # Test 8: Invalid Evidence Reference Test
    # -------------------------------------------------------------------------
    def test_8_invalid_evidence_reference(self):
        p = self._setup_base_project("p8")
        con_engine = ContradictionEngine(self.db)

        bogus_ev1 = EvidenceItem(
            id="BOGUS_1", project_id=p.id, claim_id=None, source_type="MB_RECORD", source_id="B1",
            observation="Fake", value=None, unit=None, timestamp=None, location=None,
            confidence=1.0, reliability="HIGH", relationship="SUPPORTS"
        )
        bogus_ev2 = EvidenceItem(
            id="BOGUS_2", project_id=p.id, claim_id=None, source_type="PHYSICAL_INSPECTION", source_id="B2",
            observation="Fake", value=None, unit=None, timestamp=None, location=None,
            confidence=1.0, reliability="HIGH", relationship="CONTRADICTS"
        )

        with self.assertRaises(ValueError):
            con_engine.evaluate_contradictions(
                investigation_id="inv8", project_id=p.id, claim_id=None,
                evidence_items=[bogus_ev1, bogus_ev2]
            )

    # -------------------------------------------------------------------------
    # Test 9: Unauthorized Write Attempt Test (RLS Verification)
    # -------------------------------------------------------------------------
    def test_9_unauthorized_write_attempt(self):
        p = self._setup_base_project("p9")
        hc = HumanCorrection(
            id="hc9", investigation_id="inv9", project_id=p.id, claim_id=None,
            corrected_by="Malicious User", original_interpretation="Original",
            corrected_interpretation="Forged", reason_for_correction="Hack",
            evidence_ids_involved=[]
        )

        # Attempt to save human correction as ordinary citizen / public user
        with self.assertRaises(UnauthorizedWriteError):
            self.db.save_human_correction(hc, user_role="public")

    # -------------------------------------------------------------------------
    # Test 10: Invalid Investigation State Transition Test
    # -------------------------------------------------------------------------
    def test_10_invalid_state_transition(self):
        p = self._setup_base_project("p10")
        orchestrator = Orchestrator(self.db)

        # Attempt illegal state jump from CREATED directly to CLOSED
        with self.assertRaises(ValueError):
            orchestrator.validate_transition(InvestigationState.CREATED, InvestigationState.CLOSED)


if __name__ == "__main__":
    unittest.main()
