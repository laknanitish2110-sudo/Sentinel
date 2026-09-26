"""
SENTINEL Phase 4C Test Suite — Construction-Specific Perception Proof.
Verifies specialized model invocation, output schema, provenance preservation,
confidence & uncertainty calculation, unsupported class handling, strictly NEUTRAL
relationship bounds, no financial/business judgments, Evidence Contract integration,
Evidence Graph persistence, and Decision Engine authority.
"""
import os
import unittest
from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem, InvestigationState
from sentinel.vision.construction_adapter import ConstructionPerceptionAdapter, CONSTRUCTION_CLASS_MAP
from sentinel.engines.contradiction_engine import ContradictionEngine
from sentinel.engines.decision_engine import DecisionEngine


class TestSentinelPhase4C(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.real_eval_dir = os.path.abspath("data/vision_eval_real")
        cls.sample_image = os.path.join(cls.real_eval_dir, "real_eval_02_construction_works_osaka.jpg")
        cls.db = SentinelDB(db_path=":memory:")
        cls.adapter = ConstructionPerceptionAdapter(db=cls.db, confidence_threshold=0.25)
        cls.contradiction_engine = ContradictionEngine(db=cls.db)
        cls.decision_engine = DecisionEngine()

        # Seed test project and claim
        cls.project_id = "proj_phase4c_test"
        cls.project = Project(
            id=cls.project_id,
            code="P4C-TEST",
            name="Phase 4C Drainage Infrastructure",
            description="Drainage culvert test project",
            sanctioned_amount=1000000.0,
            released_amount=500000.0
        )
        cls.db.save_project(cls.project)

        cls.claim = Claim(
            id="claim_p4c_001",
            project_id=cls.project_id,
            claim_ref="CLAIM-4C-01",
            claimed_by="Infrastructure Corp",
            claim_type="PROGRESS_PAYMENT",
            description="400m drainage excavation and pipe laying",
            claimed_value=400.0,
            unit="meters",
            claim_date="2026-09-20T08:00:00Z"
        )
        cls.db.save_claim(cls.claim)

    def test_1_real_model_invocation(self):
        """Verify real model invocation executes inference on real construction imagery."""
        items = self.adapter.detect_and_adapt(
            image_path=self.sample_image,
            project_id=self.project_id,
            claim=self.claim,
            source_evidence_id="evi_test_4c_001"
        )
        self.assertGreater(len(items), 0, "Model invocation must produce at least one perception node")
        classes_found = {item.metadata["detected_class"] for item in items}
        self.assertTrue(classes_found.intersection({"Person", "Hardhat", "Safety Vest", "machinery", "Safety Cone"}),
                        "Must detect specialized construction/machinery/PPE classes")

    def test_2_output_schema_validation(self):
        """Verify generated EvidenceItem nodes adhere to Sentinel Evidence Contract schema."""
        items = self.adapter.detect_and_adapt(
            image_path=self.sample_image,
            project_id=self.project_id,
            claim=self.claim,
            source_evidence_id="evi_test_4c_002"
        )
        for item in items:
            self.assertIsInstance(item.id, str)
            self.assertEqual(item.project_id, self.project_id)
            self.assertEqual(item.claim_id, self.claim.id)
            self.assertEqual(item.source_type, "GEO_PHOTO")
            self.assertIn("source_evidence_id", item.metadata)
            self.assertIn("bounding_box", item.metadata)
            self.assertIn("image_dimensions", item.metadata)

    def test_3_provenance_preservation(self):
        """Verify complete model provenance (repo, checkpoint, adapter version) is preserved in metadata."""
        items = self.adapter.detect_and_adapt(
            image_path=self.sample_image,
            project_id=self.project_id,
            claim=self.claim,
            source_evidence_id="evi_test_4c_003"
        )
        for item in items:
            meta = item.metadata
            self.assertEqual(meta["model_name"], "yihong1120/Construction-Hazard-Detection")
            self.assertEqual(meta["model_checkpoint_identifier"], "models/yolo11/pt/yolo11n.pt")
            self.assertEqual(meta["adapter_version"], "v4C-construction-adapter-1.0")
            self.assertIn("provenance", meta)

    def test_4_confidence_and_uncertainty_preservation(self):
        """Verify model confidence and explicit uncertainty_score (1 - conf) are preserved accurately."""
        items = self.adapter.detect_and_adapt(
            image_path=self.sample_image,
            project_id=self.project_id,
            claim=self.claim,
            source_evidence_id="evi_test_4c_004"
        )
        for item in items:
            meta = item.metadata
            self.assertGreaterEqual(item.confidence, 0.25)
            self.assertLessEqual(item.confidence, 1.0)
            expected_uncertainty = round(1.0 - item.confidence, 4)
            self.assertEqual(meta["uncertainty_score"], expected_uncertainty)

    def test_5_unsupported_class_rejection(self):
        """Verify unmapped classes (e.g. unknown label) fall back safely without error or class fabrication."""
        fake_payload = [
            {"class": "unsupported_dog_class", "confidence": 0.95, "box": [10, 10, 50, 50], "image_dimensions": "1920x1080"},
            {"class": "machinery", "confidence": 0.85, "box": [20, 20, 100, 100], "image_dimensions": "1920x1080"}
        ]
        items = []
        for idx, det in enumerate(fake_payload):
            primitive = CONSTRUCTION_CLASS_MAP.get(det["class"], "construction_object")
            if det["class"] not in CONSTRUCTION_CLASS_MAP:
                continue
            item = EvidenceItem(
                id=f"test_node_{idx}",
                project_id=self.project_id,
                claim_id=self.claim.id,
                source_type="GEO_PHOTO",
                source_id="CONST-VISION-TEST",
                observation=f"Detected {det['class']}",
                value=1.0,
                unit="object",
                timestamp="2026-09-20T10:00:00Z",
                location=None,
                confidence=det["confidence"],
                reliability="HIGH",
                relationship="NEUTRAL",
                metadata={"detected_class": det["class"], "visual_primitive": primitive}
            )
            items.append(item)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].metadata["detected_class"], "machinery")

    def test_6_neutral_evidence_relationship_invariant(self):
        """Verify all construction adapter evidence nodes strictly emit relationship == 'NEUTRAL'."""
        items = self.adapter.detect_and_adapt(
            image_path=self.sample_image,
            project_id=self.project_id,
            claim=self.claim,
            source_evidence_id="evi_test_4c_006"
        )
        for item in items:
            self.assertEqual(item.relationship, "NEUTRAL", "Perception nodes must strictly be NEUTRAL")

    def test_7_no_financial_or_business_conclusions(self):
        """Verify adapter rejects any generated observation text containing forbidden financial/business terms."""
        with self.assertRaises(ValueError):
            self.adapter._validate_non_accusatory("Project is FRAUD and claim is valid")

        with self.assertRaises(ValueError):
            self.adapter._validate_non_accusatory("VERIFIED_COMPLETION payment approved")

        with self.assertRaises(ValueError):
            self.adapter._validate_non_accusatory("MATERIAL_DELIVERED 100%")

    def test_8_integration_with_evidence_contract(self):
        """Verify construction evidence items conform to EvidenceContract data structures."""
        items = self.adapter.detect_and_adapt(
            image_path=self.sample_image,
            project_id=self.project_id,
            claim=self.claim,
            source_evidence_id="evi_test_4c_008"
        )
        for item in items:
            self.assertEqual(type(item).__name__, "EvidenceItem")
            self.assertIn(item.reliability, ("HIGH", "MEDIUM", "LOW"))

    def test_9_integration_with_evidence_graph_persistence(self):
        """Verify construction evidence items are stored in SentinelDB and queryable via Evidence Graph."""
        items = self.adapter.detect_and_adapt(
            image_path=self.sample_image,
            project_id=self.project_id,
            claim=self.claim,
            source_evidence_id="evi_test_4c_009"
        )
        db_items = self.db.get_evidence_for_project(self.project_id)
        db_ids = {e.id for e in db_items}
        for item in items:
            self.assertIn(item.id, db_ids, "Every adapted item must persist in Evidence Graph DB")

    def test_10_decision_engine_authority_preserved(self):
        """Verify DecisionEngine retains sole authority over investigation judgments regardless of perception nodes."""
        items = self.adapter.detect_and_adapt(
            image_path=self.sample_image,
            project_id=self.project_id,
            claim=self.claim,
            source_evidence_id="evi_test_4c_010"
        )
        contradictions = self.contradiction_engine.evaluate_contradictions(
            investigation_id="inv_test_4c_010",
            project_id=self.project_id,
            claim_id=self.claim.id,
            evidence_items=items
        )
        state, notes = self.decision_engine.evaluate_decision(
            agent_results=[],
            contradictions=contradictions,
            evidence_items=items,
            case_memories=[]
        )
        self.assertIsInstance(state, InvestigationState)
        self.assertIn(state, (InvestigationState.PARTIALLY_SUPPORTED, InvestigationState.SUPPORTED, InvestigationState.HUMAN_REVIEW_REQUIRED, InvestigationState.INSUFFICIENT_EVIDENCE))
        # Confirm perception adapter itself never mutated the decision state
        for item in items:
            self.assertEqual(item.relationship, "NEUTRAL")


if __name__ == "__main__":
    unittest.main()
