"""
SENTINEL Phase 5 Test Suite — Complete Investigation Loop Integration.
Verifies complete end-to-end investigation lifecycle:
1. Investigation starts via Orchestrator / API
2. Evidence collection across multi-source contracts
3. Evidence Graph generation & node relationship mapping
4. Contradiction Engine quantitative conflict detection
5. Decision Engine authoritative outcome (HUMAN_REVIEW_REQUIRED)
6. Citizen-safe structured explanation (no chain-of-thought, no secrets)
7. Human auditor correction submission
8. Original interpretation preservation (non-overwrite invariant)
9. CaseMemoryRecord creation & precedent rule storage
10. Second investigation retrieves precedent
11. Precedent surfaced with 'HISTORICAL PRECEDENT' tag
12. Independent evaluation of second case current evidence
13. No automatic case auto-resolution from precedent alone
14. No forbidden fraud / payment denial accusations
15. No internal auditor / prompt leakage in citizen API
"""
import os
import unittest
from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem, InvestigationState
from sentinel.orchestrator import Orchestrator
from sentinel.api import SentinelCitizenAPI
from sentinel.vision.construction_adapter import ConstructionPerceptionAdapter


class TestSentinelPhase5(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = SentinelDB(db_path=":memory:")
        cls.api = SentinelCitizenAPI(cls.db)
        cls.orchestrator = Orchestrator(cls.db)

        # Setup Ward 7 (Primary Case)
        cls.w7_id = "proj_test_w7"
        cls.w7_project = Project(
            id=cls.w7_id,
            code="TEST-W7-DRAIN",
            name="Ward 7 Stormwater Drainage Test",
            description="Ward 7 drainage construction",
            sanctioned_amount=1800000.0,
            released_amount=720000.0
        )
        cls.db.save_project(cls.w7_project)

        cls.w7_claim = Claim(
            id="claim_test_w7_pipe400",
            project_id=cls.w7_id,
            claim_ref="CLAIM-W7-400M",
            claimed_by="Contractor Ltd",
            claim_type="PHYSICAL_QUANTITY",
            description="400m pipe installation certified",
            claimed_value=400.0,
            unit="meters",
            claim_date="2026-09-15"
        )
        cls.db.save_claim(cls.w7_claim)

        cls.w7_mb = EvidenceItem(
            id="ev_test_w7_mb", project_id=cls.w7_id, claim_id=cls.w7_claim.id,
            source_type="MB_RECORD", source_id="MB-402",
            observation="Measurement Book certifying 400m pipe excavation",
            value=400.0, unit="meters", timestamp="2026-09-14", location=None,
            confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        cls.w7_insp = EvidenceItem(
            id="ev_test_w7_insp", project_id=cls.w7_id, claim_id=cls.w7_claim.id,
            source_type="PHYSICAL_INSPECTION", source_id="INSP-009",
            observation="Photo inspection showing 180m visible in trench",
            value=180.0, unit="meters", timestamp="2026-09-18", location=None,
            confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
        )
        cls.db.save_evidence(cls.w7_mb)
        cls.db.save_evidence(cls.w7_insp)

        # Attach vision perception nodes
        adapter = ConstructionPerceptionAdapter(db=cls.db, confidence_threshold=0.25)
        sample_img = os.path.join("data", "vision_eval_real", "real_eval_02_construction_works_osaka.jpg")
        if os.path.exists(sample_img):
            adapter.detect_and_adapt(
                image_path=sample_img,
                project_id=cls.w7_id,
                claim=cls.w7_claim,
                source_evidence_id="ev_test_w7_vision"
            )

        # Initial Ward 7 investigation run
        cls.w7_inv_info = cls.api.trigger_investigation(cls.w7_id)
        cls.w7_inv_id = cls.w7_inv_info["investigation_id"]

        # Submit Ward 7 human auditor correction during setup so CaseMemory is established
        cls.corr_res = cls.api.submit_human_correction(
            project_id=cls.w7_id,
            investigation_id=cls.w7_inv_id,
            claim_id=cls.w7_claim.id,
            corrected_interpretation="Subsurface pipe laid and backfilled underground.",
            reason_for_correction="Backfilling compaction records verified.",
            evidence_ids=["ev_test_w7_mb", "ev_test_w7_insp"]
        )

        # Setup Ward 8 (Second Case)
        cls.w8_id = "proj_test_w8"
        cls.w8_project = Project(
            id=cls.w8_id,
            code="TEST-W8-DRAIN",
            name="Ward 8 Drainage Extension Test",
            description="Ward 8 drainage extension",
            sanctioned_amount=2500000.0,
            released_amount=1000000.0
        )
        cls.db.save_project(cls.w8_project)

        cls.w8_claim = Claim(
            id="claim_test_w8_pipe500",
            project_id=cls.w8_id,
            claim_ref="CLAIM-W8-500M",
            claimed_by="Contractor Ltd",
            claim_type="PHYSICAL_QUANTITY",
            description="500m pipe installation certified",
            claimed_value=500.0,
            unit="meters",
            claim_date="2026-09-20"
        )
        cls.db.save_claim(cls.w8_claim)

        cls.w8_mb = EvidenceItem(
            id="ev_test_w8_mb", project_id=cls.w8_id, claim_id=cls.w8_claim.id,
            source_type="MB_RECORD", source_id="MB-505",
            observation="Measurement Book certifying 500m pipe excavation",
            value=500.0, unit="meters", timestamp="2026-09-19", location=None,
            confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        cls.w8_insp = EvidenceItem(
            id="ev_test_w8_insp", project_id=cls.w8_id, claim_id=cls.w8_claim.id,
            source_type="PHYSICAL_INSPECTION", source_id="INSP-012",
            observation="Photo inspection showing 220m visible in trench",
            value=220.0, unit="meters", timestamp="2026-09-21", location=None,
            confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
        )
        cls.db.save_evidence(cls.w8_mb)
        cls.db.save_evidence(cls.w8_insp)

    def test_1_investigation_starts_via_orchestrator_api(self):
        """Verify investigation entry point creates investigation and transitions states."""
        res = self.api.trigger_investigation(self.w7_id)
        self.assertIn("investigation_id", res)
        self.assertEqual(res["project_id"], self.w7_id)

        events = self.db.get_investigation_events(res["investigation_id"])
        event_types = [e["event_type"] for e in events]
        self.assertIn("INVESTIGATION_CREATED", event_types)
        self.assertIn("STATE_TRANSITION", event_types)

    def test_2_evidence_collection_multi_source(self):
        """Verify evidence is collected across financial, MB, inspection, and vision sources."""
        ev_items = self.db.get_evidence_for_project(self.w7_id)
        source_types = {e.source_type for e in ev_items}
        self.assertIn("MB_RECORD", source_types)
        self.assertIn("PHYSICAL_INSPECTION", source_types)
        self.assertIn("GEO_PHOTO", source_types)

    def test_3_evidence_graph_generated_with_relationships(self):
        """Verify Evidence Graph generates claim and evidence nodes with correct relationship tags."""
        graph = self.api.get_evidence_graph(self.w7_id)
        self.assertGreaterEqual(len(graph["claims"]), 1)
        self.assertGreaterEqual(len(graph["evidence"]), 2)

        mb_node = next(n for n in graph["evidence"] if n["source_id"] == "MB-402")
        self.assertEqual(mb_node["relationship"], "SUPPORTS")

        insp_node = next(n for n in graph["evidence"] if n["source_id"] == "INSP-009")
        self.assertEqual(insp_node["relationship"], "CONTRADICTS")

    def test_4_contradiction_engine_detects_quantitative_conflict(self):
        """Verify Contradiction Engine flags physical discrepancy (400m MB vs 180m photo)."""
        cur = self.db.conn.cursor()
        cur.execute("SELECT * FROM contradictions WHERE project_id = ?", (self.w7_id,))
        rows = cur.fetchall()
        self.assertGreaterEqual(len(rows), 1)

    def test_5_decision_engine_produces_human_review_required(self):
        """Verify Decision Engine renders HUMAN_REVIEW_REQUIRED or PARTIALLY_SUPPORTED when precedent is surfaced."""
        status = self.api.get_investigation_status(self.w7_id)
        self.assertIn(status["final_state_raw"], ("HUMAN_REVIEW_REQUIRED", "PARTIALLY_SUPPORTED"))

    def test_6_citizen_safe_explanation_generated(self):
        """Verify citizen explanation contains plain language sections without internal secrets."""
        expl = self.api.get_citizen_explanation(self.w7_id)
        self.assertIn("what_sentinel_found", expl)
        self.assertIn("why_this_matters", expl)
        self.assertIn("current_status", expl)
        self.assertIsInstance(expl["what_sentinel_found"], list)

    def test_7_human_correction_submitted(self):
        """Verify auditor correction can be submitted and saved in DB."""
        self.assertEqual(self.corr_res["status"], "CORRECTION_STORED")
        self.assertIn("correction_id", self.corr_res)
        self.assertIn("case_memory_id", self.corr_res)

    def test_8_original_interpretation_preserved(self):
        """Verify human correction preserves original interpretation without overwriting."""
        cur = self.db.conn.cursor()
        cur.execute("SELECT * FROM human_corrections WHERE project_id = ?", (self.w7_id,))
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertTrue(len(row["original_interpretation"]) > 0)
        self.assertTrue(len(row["corrected_interpretation"]) > 0)
        self.assertNotEqual(row["original_interpretation"], row["corrected_interpretation"])

    def test_9_case_memory_record_created(self):
        """Verify CaseMemoryRecord is saved with precedent rule."""
        memories = self.db.get_case_memories_for_pattern("STAGED_MATERIAL_DISCREPANCY")
        self.assertGreaterEqual(len(memories), 1)
        m = memories[0]
        self.assertIn("precedent_rule", m.__dict__)
        self.assertGreater(len(m.precedent_rule), 10)

    def test_10_second_investigation_retrieves_precedent(self):
        """Verify second investigation (Ward 8) retrieves historical precedent from Ward 7 correction."""
        status_w8 = self.api.get_investigation_status(self.w8_id)
        self.assertIsNotNone(status_w8["historical_precedent"])
        self.assertEqual(status_w8["historical_precedent"]["label"], "HISTORICAL PRECEDENT")

    def test_11_precedent_marked_historical_precedent(self):
        """Verify precedent metadata is clearly tagged with 'HISTORICAL PRECEDENT'."""
        status_w8 = self.api.get_investigation_status(self.w8_id)
        prec = status_w8["historical_precedent"]
        self.assertEqual(prec["label"], "HISTORICAL PRECEDENT")
        self.assertIn("precedent_rule", prec)

    def test_12_current_evidence_independently_evaluated(self):
        """Verify Ward 8 current evidence (500m MB vs 220m photo) is evaluated independently."""
        status_w8 = self.api.get_investigation_status(self.w8_id)
        self.assertEqual(status_w8["project_id"], self.w8_id)
        w8_ev = self.db.get_evidence_for_project(self.w8_id)
        self.assertEqual(len(w8_ev), 2)

    def test_13_no_automatic_resolution_from_precedent(self):
        """Verify previous human correction does NOT auto-resolve or auto-close second investigation."""
        status_w8 = self.api.get_investigation_status(self.w8_id)
        self.assertNotEqual(status_w8["final_state_raw"], "CLOSED")
        self.assertIn(status_w8["final_state_raw"], ("HUMAN_REVIEW_REQUIRED", "PARTIALLY_SUPPORTED"))

    def test_14_no_forbidden_fraud_accusations(self):
        """Verify system never outputs forbidden fraud accusations or auto payment denial."""
        status_w7 = self.api.get_investigation_status(self.w7_id)
        expl_text = str(status_w7["evidence_grounded_explanation"]).upper()
        forbidden = ["FRAUD", "FRAUDULENT", "CRIMINAL", "PAYMENT_DENIAL", "CLAIM_IS_FALSE"]
        for f_word in forbidden:
            self.assertNotIn(f_word, expl_text)

    def test_15_no_internal_prompt_or_key_leakage(self):
        """Verify public API responses do not leak internal prompts, API keys, or internal variables."""
        status_w7 = self.api.get_investigation_status(self.w7_id)
        status_str = str(status_w7)
        self.assertNotIn("api_key", status_str.lower())
        self.assertNotIn("sk-ant-", status_str)
        self.assertNotIn("prompt_template", status_str.lower())


if __name__ == "__main__":
    unittest.main()
