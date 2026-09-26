"""
SENTINEL Phase 2A Automated Test Suite.
Covers 8 mandatory test scenarios for citizen experience, API data matching, evidence graph node rendering, and security isolation.
"""
import unittest
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem, HumanCorrection, CaseMemoryRecord
from sentinel.api import SentinelCitizenAPI


class TestSentinelPhase2A(unittest.TestCase):

    def setUp(self):
        self.db = SentinelDB(":memory:")
        self.project_id = "p-demo-2a"
        p = Project(
            id=self.project_id,
            code="DEMO-WARD7-DRAIN-2026",
            name="Ward 7 Drainage Improvement [DEMO DATA]",
            description="Construction of RCC storm water drain and laying of 400m main drainage line.",
            sanctioned_amount=1800000.0,
            released_amount=720000.0,
            currency="INR",
            location_name="Ward 7 Arterial Corridor",
            status="UNDER_AUDIT",
            metadata={"is_demo_data": True}
        )
        self.db.save_project(p)

        self.claim1 = Claim(
            id="c1-ra2", project_id=p.id, claim_ref="CLAIM-WARD7-RA-02", claimed_by="Apex Infra Works Ltd",
            claim_type="COMPLETION_PERCENTAGE", description="2nd RA Bill claiming 80% completion.",
            claimed_value=80.0, unit="percent", claim_date="2026-09-15"
        )
        self.claim2 = Claim(
            id="c2-pipe400", project_id=p.id, claim_ref="CLAIM-WARD7-PIPE-400M", claimed_by="Apex Infra Works Ltd",
            claim_type="PHYSICAL_QUANTITY", description="Full installation of 400m hume pipes.",
            claimed_value=400.0, unit="meters", claim_date="2026-09-15"
        )
        self.db.save_claim(self.claim1)
        self.db.save_claim(self.claim2)

        self.ev1 = EvidenceItem(
            id="e1-mb", project_id=p.id, claim_id=self.claim2.id, source_type="MB_RECORD", source_id="MB-402",
            observation="JE cert 400m pipe installation completed.", value=400.0, unit="meters",
            timestamp="2026-09-14", location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )
        self.ev2 = EvidenceItem(
            id="e2-photo", project_id=p.id, claim_id=self.claim2.id, source_type="PHYSICAL_INSPECTION", source_id="INSP-009",
            observation="Site photo inspection verified only 180m pipe laid in active trench.", value=180.0, unit="meters",
            timestamp="2026-09-18", location={"address": "Section B"}, confidence=0.90, reliability="HIGH", relationship="CONTRADICTS"
        )
        self.ev3 = EvidenceItem(
            id="e3-inv", project_id=p.id, claim_id=self.claim2.id, source_type="INVOICE", source_id="INV-9941",
            observation="Invoice confirms procurement and delivery of 400m hume pipes to site.", value=400.0, unit="meters",
            timestamp="2026-09-02", location=None, confidence=0.98, reliability="HIGH", relationship="NEUTRAL", metadata={"invoice_amount": 480000.0}
        )
        self.ev4 = EvidenceItem(
            id="e4-bank", project_id=p.id, claim_id=self.claim1.id, source_type="BANK_STATEMENT", source_id="TREASURY-02",
            observation="Treasury records confirm Tranche 1 release (₹7,20,000).", value=720000.0, unit="INR",
            timestamp="2026-08-10", location=None, confidence=0.95, reliability="HIGH", relationship="SUPPORTS"
        )

        self.db.save_evidence(self.ev1)
        self.db.save_evidence(self.ev2)
        self.db.save_evidence(self.ev3)
        self.db.save_evidence(self.ev4)

        self.api = SentinelCitizenAPI(self.db)

    def tearDown(self):
        self.db.close()

    # -------------------------------------------------------------------------
    # Test 1: Project Loads Test
    # -------------------------------------------------------------------------
    def test_1_project_loads(self):
        data = self.api.get_public_project(self.project_id)
        self.assertEqual(data["code"], "DEMO-WARD7-DRAIN-2026")
        self.assertEqual(data["name"], "Ward 7 Drainage Improvement [DEMO DATA]")
        self.assertEqual(data["sanctioned_amount"], 1800000.0)
        self.assertEqual(data["released_amount"], 720000.0)
        self.assertEqual(data["status"], "Under Active Verification")

    # -------------------------------------------------------------------------
    # Test 2: Money Trail Values Match Database Test
    # -------------------------------------------------------------------------
    def test_2_money_trail_values_match_db(self):
        trail = self.api.get_money_trail(self.project_id)
        self.assertEqual(trail["sanctioned_amount"], 1800000.0)
        self.assertEqual(trail["released_amount"], 720000.0)
        self.assertEqual(trail["claimed_amount"], 1440000.0)  # 80% of 18L
        self.assertEqual(len(trail["financial_evidence"]), 3)

    # -------------------------------------------------------------------------
    # Test 3: Evidence Relationships Render Correctly Test
    # -------------------------------------------------------------------------
    def test_3_evidence_relationships_render_correctly(self):
        graph = self.api.get_evidence_graph(self.project_id)
        ev_nodes = graph["evidence"]
        self.assertEqual(len(ev_nodes), 4)

        relationships = {e["relationship"] for e in ev_nodes}
        self.assertEqual(relationships, {"SUPPORTS", "CONTRADICTS", "NEUTRAL"})

        for node in ev_nodes:
            self.assertIn("badge_icon", node)
            self.assertIn("relationship_label", node)

    # -------------------------------------------------------------------------
    # Test 4: Contradiction Appears Correctly Test
    # -------------------------------------------------------------------------
    def test_4_contradiction_appears_correctly(self):
        graph = self.api.get_evidence_graph(self.project_id)
        con_node = next(e for e in graph["evidence"] if e["relationship"] == "CONTRADICTS")
        self.assertEqual(con_node["source_id"], "INSP-009")
        self.assertIn("180m pipe", con_node["observation"])
        self.assertEqual(con_node["badge_icon"], "✕")

    # -------------------------------------------------------------------------
    # Test 5: Human Review State Renders Correctly Test
    # -------------------------------------------------------------------------
    def test_5_human_review_state_renders_correctly(self):
        status = self.api.get_investigation_status(self.project_id)
        self.assertIn("HUMAN REVIEW REQUIRED", status["final_state"])
        self.assertIsNotNone(status["human_review_notice"])
        self.assertIn("cannot resolve the difference automatically", status["human_review_notice"])

    # -------------------------------------------------------------------------
    # Test 6: Internal Fields Are Not Exposed Test
    # -------------------------------------------------------------------------
    def test_6_internal_fields_not_exposed(self):
        status_json = json.dumps(self.api.get_investigation_status(self.project_id))
        self.assertNotIn("prompt", status_json.lower())
        self.assertNotIn("chain_of_thought", status_json.lower())
        self.assertNotIn("api_key", status_json.lower())
        self.assertNotIn("jwt", status_json.lower())

    # -------------------------------------------------------------------------
    # Test 7: No Forbidden Fraud/Accusation Messaging Test
    # -------------------------------------------------------------------------
    def test_7_no_forbidden_fraud_messaging(self):
        all_text = (
            json.dumps(self.api.get_public_project(self.project_id)) +
            json.dumps(self.api.get_money_trail(self.project_id)) +
            json.dumps(self.api.get_evidence_graph(self.project_id)) +
            json.dumps(self.api.get_investigation_status(self.project_id))
        ).lower()

        forbidden_words = ["fraud", "guilty", "scam", "deny payment", "criminal"]
        for word in forbidden_words:
            self.assertNotIn(word, all_text, f"Forbidden word '{word}' found in citizen API output.")

    # -------------------------------------------------------------------------
    # Test 8: End-to-End Case Memory Precedent Render Test
    # -------------------------------------------------------------------------
    def test_8_case_memory_precedent_render(self):
        inv_id = self.db.create_investigation(self.project_id, "Inv 2A", user_role="service_role")
        hc = HumanCorrection(
            id="hc-2a", investigation_id=inv_id, project_id=self.project_id, claim_id=self.claim2.id,
            corrected_by="Auditor", original_interpretation="Unexecuted work",
            corrected_interpretation="Staged material", reason_for_correction="Material staged in yard",
            evidence_ids_involved=[self.ev1.id, self.ev2.id]
        )
        self.db.save_human_correction(hc, user_role="auditor")

        cm = CaseMemoryRecord(
            id="cm-2a", human_correction_id=hc.id, investigation_id=inv_id, project_id=self.project_id,
            pattern_type="STAGED_MATERIAL_DISCREPANCY",
            context_summary="Trench photo omits yard",
            precedent_rule="Check delivery bills for site staging yard.",
            lessons_learned="Yard staging explains trench variance."
        )
        self.db.save_case_memory(cm, user_role="service_role")

        status = self.api.get_investigation_status(self.project_id)
        self.assertIsNotNone(status["learned_case_memory"])
        self.assertEqual(status["learned_case_memory"]["pattern_type"], "STAGED_MATERIAL_DISCREPANCY")
        self.assertIn("Sentinel Learned", status["learned_case_memory"]["title"])


if __name__ == "__main__":
    unittest.main()
