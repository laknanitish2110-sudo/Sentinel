"""
SENTINEL P0 Fixes Test Suite — Investigation Idempotency & Decision Priority.
Verifies:
A. Calling investigation status repeatedly does NOT create new investigation records.
B. Calling investigation status does NOT execute the orchestrator.
C. Ward 7 with strong contradiction + insufficient evidence returns HUMAN_REVIEW_REQUIRED.
D. Genuinely insufficient-only case (no contradiction) returns INSUFFICIENT_EVIDENCE.
E. Existing human correction and case-memory behavior remains intact.
"""
import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import unittest
from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem, InvestigationState, ContradictionRecord
from sentinel.orchestrator import Orchestrator
from sentinel.api import SentinelCitizenAPI
from sentinel.engines.decision_engine import DecisionEngine


class TestSentinelP0Fixes(unittest.TestCase):

    def setUp(self):
        self.db = SentinelDB(db_path=":memory:")
        self.api = SentinelCitizenAPI(self.db)
        self.orchestrator = Orchestrator(self.db)

        # Create Ward 7 Project & Claims
        self.w7_id = "proj_p0_w7"
        self.w7_proj = Project(
            id=self.w7_id, code="P0-W7-DRAIN", name="Ward 7 Drain P0 Test",
            description="Ward 7 test", sanctioned_amount=1800000.0, released_amount=720000.0
        )
        self.db.save_project(self.w7_proj)

        self.w7_claim = Claim(
            id="claim_p0_w7_pipe400", project_id=self.w7_id, claim_ref="CLAIM-W7-400M",
            claimed_by="Contractor Ltd", claim_type="PHYSICAL_QUANTITY", description="400m pipe",
            claimed_value=400.0, unit="meters", claim_date="2026-09-15"
        )
        self.db.save_claim(self.w7_claim)

        self.w7_mb = EvidenceItem(
            id="ev_p0_w7_mb", project_id=self.w7_id, claim_id=self.w7_claim.id,
            source_type="MB_RECORD", source_id="MB-402", observation="JE MB entry certifying 400m pipe laying",
            value=400.0, unit="meters", timestamp="2026-09-14", location=None,
            confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        self.w7_insp = EvidenceItem(
            id="ev_p0_w7_insp", project_id=self.w7_id, claim_id=self.w7_claim.id,
            source_type="PHYSICAL_INSPECTION", source_id="INSP-009", observation="Inspection photo showing 180m visible",
            value=180.0, unit="meters", timestamp="2026-09-18", location=None,
            confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
        )
        self.w7_bank = EvidenceItem(
            id="ev_p0_w7_bank", project_id=self.w7_id, claim_id=self.w7_claim.id,
            source_type="BANK_STATEMENT", source_id="TREASURY-01", observation="Treasury voucher missing clearance certificate",
            value=720000.0, unit="INR", timestamp="2026-08-10", location=None,
            confidence=0.50, reliability="UNVERIFIED", relationship="INSUFFICIENT"
        )
        self.db.save_evidence(self.w7_mb)
        self.db.save_evidence(self.w7_insp)
        self.db.save_evidence(self.w7_bank)

    def test_A_repeated_status_calls_do_not_create_new_investigation_records(self):
        """A. Verify calling investigation status repeatedly does not create new investigation records."""
        # Initial trigger creates 1 investigation
        trig_res = self.api.trigger_investigation(self.w7_id)
        inv_id = trig_res["investigation_id"]

        cur = self.db.conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM investigations WHERE project_id = ?", (self.w7_id,))
        count_after_trigger = cur.fetchone()["cnt"]
        self.assertEqual(count_after_trigger, 1)

        # Call get_investigation_status 10 times
        for _ in range(10):
            res = self.api.get_investigation_status(self.w7_id)
            self.assertEqual(res["investigation_id"], inv_id)

        cur.execute("SELECT COUNT(*) as cnt FROM investigations WHERE project_id = ?", (self.w7_id,))
        count_after_status_calls = cur.fetchone()["cnt"]
        self.assertEqual(count_after_status_calls, 1)

    def test_B_status_calls_do_not_execute_orchestrator(self):
        """B. Verify calling investigation status does not execute the orchestrator."""
        self.api.trigger_investigation(self.w7_id)

        # Count events before status calls
        cur = self.db.conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM investigation_events")
        events_before = cur.fetchone()["cnt"]

        # Call status repeatedly
        self.api.get_investigation_status(self.w7_id)
        self.api.get_investigation_status(self.w7_id)

        cur.execute("SELECT COUNT(*) as cnt FROM investigation_events")
        events_after = cur.fetchone()["cnt"]
        self.assertEqual(events_before, events_after)

    def test_C_ward7_contradiction_plus_insufficient_returns_human_review_required(self):
        """C. Verify Ward 7 with strong contradiction + insufficient evidence returns HUMAN_REVIEW_REQUIRED."""
        res = self.api.trigger_investigation(self.w7_id)
        self.assertEqual(res["final_state_raw"], "HUMAN_REVIEW_REQUIRED")
        self.assertIsNotNone(res["human_review_notice"])

    def test_D_genuinely_insufficient_only_case_returns_insufficient_evidence(self):
        """D. Verify a case with ONLY insufficient evidence (no high severity contradiction) returns INSUFFICIENT_EVIDENCE."""
        p_insuff_id = "proj_p0_insuff_only"
        p_insuff = Project(
            id=p_insuff_id, code="P0-INSUFF-ONLY", name="Insufficient Only Test",
            description="No contradiction, missing docs", sanctioned_amount=100000.0, released_amount=0.0
        )
        self.db.save_project(p_insuff)

        c_insuff = Claim(
            id="claim_insuff", project_id=p_insuff_id, claim_ref="CLAIM-INSUFF-1",
            claimed_by="Contractor Ltd", claim_type="COMPLETION_PERCENTAGE", description="Claim 50%",
            claimed_value=50.0, unit="percent", claim_date="2026-09-20"
        )
        self.db.save_claim(c_insuff)

        e_insuff = EvidenceItem(
            id="ev_insuff_bank", project_id=p_insuff_id, claim_id=c_insuff.id,
            source_type="BANK_STATEMENT", source_id="BANK-UNVERIFIED", observation="Missing bank voucher",
            value=50000.0, unit="INR", timestamp="2026-09-20", location=None,
            confidence=0.40, reliability="UNVERIFIED", relationship="INSUFFICIENT"
        )
        self.db.save_evidence(e_insuff)

        res = self.api.trigger_investigation(p_insuff_id)
        self.assertEqual(res["final_state_raw"], "INSUFFICIENT_EVIDENCE")

    def test_E_human_correction_and_case_memory_behavior_intact(self):
        """E. Verify existing human correction and case memory behavior remains fully intact."""
        trig_res = self.api.trigger_investigation(self.w7_id)
        inv_id = trig_res["investigation_id"]

        corr_res = self.api.submit_human_correction(
            project_id=self.w7_id,
            investigation_id=inv_id,
            claim_id=self.w7_claim.id,
            corrected_interpretation="Underground pipe laying verified.",
            reason_for_correction="Subsurface compaction logs confirmed.",
            evidence_ids=["ev_p0_w7_mb", "ev_p0_w7_insp"]
        )
        self.assertEqual(corr_res["status"], "CORRECTION_STORED")

        memories = self.db.get_case_memories_for_pattern("STAGED_MATERIAL_DISCREPANCY")
        self.assertGreaterEqual(len(memories), 1)


if __name__ == "__main__":
    unittest.main()
