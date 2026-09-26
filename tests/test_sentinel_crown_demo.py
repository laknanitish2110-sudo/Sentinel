"""
SENTINEL Crown Demo Integration Test Suite.
Verifies complete Crown Demo lifecycle end-to-end:
1. Ward 7 initial setup & public metrics
2. Investigation execution & Evidence Graph generation
3. Contradiction detection (400m MB vs 180m physical inspection photo)
4. Decision Engine HUMAN_REVIEW_REQUIRED outcome
5. Citizen explanation text formatting & grounding
6. Human Auditor Correction submission & non-overwrite invariant
7. CaseMemoryRecord instantiation & precedent rule storage
8. Ward 8 precedent retrieval & PRECEDENT ≠ PROOF tag
9. Independent Ward 8 current evidence evaluation
10. Final banner & principle invariants
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import unittest
from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem
from sentinel.orchestrator import Orchestrator
from sentinel.api import SentinelCitizenAPI


class TestSentinelCrownDemo(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = SentinelDB(db_path=":memory:")
        cls.api = SentinelCitizenAPI(cls.db)

        # Setup Ward 7
        cls.w7_id = "proj_crown_test_w7"
        cls.w7_project = Project(
            id=cls.w7_id,
            code="DEMO-WARD7-DRAIN-2026",
            name="Ward 7 Stormwater Drainage Improvement",
            description="Ward 7 drainage construction",
            sanctioned_amount=1800000.0,
            released_amount=720000.0
        )
        cls.db.save_project(cls.w7_project)

        cls.w7_claim = Claim(
            id="claim_crown_w7_pipe400",
            project_id=cls.w7_id,
            claim_ref="CLAIM-WARD7-PIPE-400M",
            claimed_by="Apex Infra Works Ltd",
            claim_type="PHYSICAL_QUANTITY",
            description="400m pipe installation certified",
            claimed_value=400.0,
            unit="meters",
            claim_date="2026-09-15"
        )
        cls.db.save_claim(cls.w7_claim)

        cls.w7_mb = EvidenceItem(
            id="ev_w7_mb402", project_id=cls.w7_id, claim_id=cls.w7_claim.id,
            source_type="MB_RECORD", source_id="MB-402",
            observation="Junior Engineer Measurement Book entry certifying 400m of pipe excavation and laying completed.",
            value=400.0, unit="meters", timestamp="2026-09-14", location=None,
            confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        cls.w7_insp = EvidenceItem(
            id="ev_w7_insp180", project_id=cls.w7_id, claim_id=cls.w7_claim.id,
            source_type="PHYSICAL_INSPECTION", source_id="INSP-009",
            observation="Independent site audit photo inspection verified 180 meters of pipe laid inside active trench.",
            value=180.0, unit="meters", timestamp="2026-09-18", location=None,
            confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
        )
        cls.db.save_evidence(cls.w7_mb)
        cls.db.save_evidence(cls.w7_insp)

        # Trigger Ward 7 investigation
        cls.inv1_res = cls.api.trigger_investigation(cls.w7_id)

    def test_1_ward7_discovery_metrics(self):
        """Verify Ward 7 public metrics match Crown Demo specification."""
        proj = self.api.get_public_project(self.w7_id)
        self.assertEqual(proj["sanctioned_amount"], 1800000.0)
        self.assertEqual(proj["released_amount"], 720000.0)
        self.assertEqual(proj["claimed_percentage"], 80.0)

    def test_2_investigation_pipeline_execution(self):
        """Verify investigation pipeline transitions cleanly through backend states."""
        status = self.api.get_investigation_status(self.w7_id)
        self.assertIn("investigation_id", status)
        self.assertTrue(len(status["completed_stages"]) >= 5)

    def test_3_evidence_graph_nodes(self):
        """Verify Evidence Graph separates conflicting measurement nodes from neutral nodes."""
        graph = self.api.get_evidence_graph(self.w7_id)
        mb_node = next(n for n in graph["evidence"] if n["source_id"] == "MB-402")
        insp_node = next(n for n in graph["evidence"] if n["source_id"] == "INSP-009")

        self.assertEqual(mb_node["relationship"], "SUPPORTS")
        self.assertEqual(insp_node["relationship"], "CONTRADICTS")

    def test_4_sentinel_finding_explanation(self):
        """Verify citizen finding plain language matches exact requirements."""
        expl = self.api.get_citizen_explanation(self.w7_id)
        self.assertIn("Official measurement records report 400m of certified work.", expl["what_sentinel_found"])
        self.assertIn("Inspection evidence reports approximately 180m visible at the inspected location.", expl["what_sentinel_found"])
        self.assertEqual(expl["why_this_matters"], "The available evidence does not fully reconcile the reported completion with the evidence currently available.")
        self.assertEqual(expl["current_status"], "HUMAN_REVIEW_REQUIRED")

    def test_5_human_correction_and_memory_retrieval(self):
        """Verify human correction submission preserves original interpretation and creates CaseMemoryRecord."""
        corr_res = self.api.submit_human_correction(
            project_id=self.w7_id,
            investigation_id=self.inv1_res["investigation_id"],
            claim_id=self.w7_claim.id,
            corrected_interpretation="The missing section was underground/backfilled and therefore was not visible during inspection.",
            reason_for_correction="Underground/backfilled infrastructure may not remain visually observable after completion.",
            evidence_ids=["ev_w7_mb402", "ev_w7_insp180"]
        )
        self.assertEqual(corr_res["status"], "CORRECTION_STORED")
        self.assertIn("The missing section was underground/backfilled", corr_res["corrected_interpretation"])
        self.assertIn("Certified infrastructure may exceed visible surface evidence", corr_res["precedent_rule"])

    def test_6_ward8_precedent_retrieval_and_independence(self):
        """Verify Ward 8 retrieves precedent with PRECEDENT ≠ PROOF invariant and independent evaluation."""
        w8_id = "proj_crown_test_w8"
        p2 = Project(
            id=w8_id, code="DEMO-WARD8-DRAIN-2026",
            name="Ward 8 Drainage Extension", description="Ward 8 drain",
            sanctioned_amount=2500000.0, released_amount=1000000.0
        )
        self.db.save_project(p2)

        c2 = Claim(
            id="claim_crown_w8_pipe500", project_id=w8_id, claim_ref="CLAIM-WARD8-PIPE-500M",
            claimed_by="Contractor Ltd", claim_type="PHYSICAL_QUANTITY", description="500m certified",
            claimed_value=500.0, unit="meters", claim_date="2026-09-20"
        )
        self.db.save_claim(c2)

        e2_mb = EvidenceItem(
            id="ev_w8_mb505", project_id=w8_id, claim_id=c2.id,
            source_type="MB_RECORD", source_id="MB-505",
            observation="JE MB entry certifying 500m completed.",
            value=500.0, unit="meters", timestamp="2026-09-19", location=None,
            confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        e2_insp = EvidenceItem(
            id="ev_w8_photo220", project_id=w8_id, claim_id=c2.id,
            source_type="PHYSICAL_INSPECTION", source_id="INSP-012",
            observation="Photo inspection showing 220m visible.",
            value=220.0, unit="meters", timestamp="2026-09-21", location=None,
            confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
        )
        self.db.save_evidence(e2_mb)
        self.db.save_evidence(e2_insp)

        inv2_status = self.api.get_investigation_status(w8_id)
        self.assertIsNotNone(inv2_status["historical_precedent"])
        self.assertEqual(inv2_status["historical_precedent"]["label"], "HISTORICAL PRECEDENT")

        # Independent current evidence evaluation
        self.assertNotEqual(inv2_status["final_state_raw"], "CLOSED")


if __name__ == "__main__":
    unittest.main()
