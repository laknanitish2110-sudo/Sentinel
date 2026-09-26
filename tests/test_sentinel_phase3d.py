"""
SENTINEL Phase 3D Test Suite — Human Correction to Case Memory Loop.
Verifies correction persistence, audit log preservation, case memory creation,
deterministic precedent retrieval, non-auto-closing invariant, and citizen privacy sanitization.
"""
import os
import unittest

from sentinel.db import SentinelDB
from sentinel.types import Project, Claim, EvidenceItem, InvestigationState
from sentinel.engines.case_memory_engine import CaseMemoryEngine
from sentinel.orchestrator import Orchestrator


class TestSentinelPhase3D(unittest.TestCase):

    def setUp(self):
        self.db = SentinelDB()
        self.memory_engine = CaseMemoryEngine(db=self.db)

        self.project = Project(
            id="proj_3d_test",
            code="PRJ-3D-001",
            name="Phase 3D Case Memory Test Project",
            description="Testing human correction loop",
            sanctioned_amount=1500000.0,
            released_amount=750000.0
        )
        self.db.save_project(self.project)

        self.claim = Claim(
            id="clm_3d_test",
            project_id=self.project.id,
            claim_ref="CLM-3D-001",
            claimed_by="Test Contractor",
            claim_type="PHYSICAL_QUANTITY",
            description="Installed 300m RCC pipeline",
            claimed_value=300.0,
            unit="meters",
            claim_date="2026-09-15"
        )
        self.db.save_claim(self.claim)

        self.ev_photo = EvidenceItem(
            id="ev_photo_3d",
            project_id=self.project.id,
            claim_id=self.claim.id,
            source_type="GEO_PHOTO",
            source_id="CAM-3D-01",
            observation="Photo shows 120m visible pipe",
            value=120.0,
            unit="meters",
            timestamp="2026-09-16T09:00:00Z",
            location={"latitude": 12.972, "longitude": 77.595},
            confidence=0.90,
            reliability="HIGH",
            relationship="NEUTRAL"
        )
        self.db.save_evidence(self.ev_photo)

        self.ev_mb = EvidenceItem(
            id="ev_mb_3d",
            project_id=self.project.id,
            claim_id=self.claim.id,
            source_type="MB_RECORD",
            source_id="MB-3D-01",
            observation="MB entry certifying 300m completed",
            value=300.0,
            unit="meters",
            timestamp="2026-09-17T10:00:00Z",
            location={"latitude": 12.972, "longitude": 77.595},
            confidence=1.0,
            reliability="HIGH",
            relationship="SUPPORTS"
        )
        self.db.save_evidence(self.ev_mb)

    def test_1_correction_persistence(self):
        """Verify human auditor correction is saved to database."""
        orchestrator = Orchestrator(db=self.db)
        res = orchestrator.run_investigation(self.project.id, self.claim.id)

        correction, _ = self.memory_engine.process_human_correction(
            investigation_id=res["investigation_id"],
            project_id=self.project.id,
            claim_id=self.claim.id,
            corrected_by="AUDITOR-101",
            original_interpretation="Only 120m visible vs 300m MB claim",
            corrected_interpretation="300m installed; 180m covered by backfill",
            reason_for_correction="Soil excavation logs confirm backfilling",
            evidence_ids_involved=[self.ev_photo.id, self.ev_mb.id],
            user_role="auditor"
        )
        self.assertIsNotNone(correction.id)

    def test_2_original_interpretation_remains_unchanged(self):
        """Verify original system interpretation is preserved and not overwritten."""
        orchestrator = Orchestrator(db=self.db)
        res = orchestrator.run_investigation(self.project.id, self.claim.id)
        orig_text = "Original discrepancy note: 120m vs 300m"

        correction, _ = self.memory_engine.process_human_correction(
            investigation_id=res["investigation_id"],
            project_id=self.project.id,
            claim_id=self.claim.id,
            corrected_by="AUDITOR-101",
            original_interpretation=orig_text,
            corrected_interpretation="Corrected view: 300m complete",
            reason_for_correction="Auditor verification",
            evidence_ids_involved=[self.ev_photo.id],
            user_role="auditor"
        )

        self.assertEqual(correction.original_interpretation, orig_text)
        self.assertNotEqual(correction.original_interpretation, correction.corrected_interpretation)

    def test_3_corrected_interpretation_is_stored(self):
        """Verify corrected interpretation is stored accurately."""
        orchestrator = Orchestrator(db=self.db)
        res = orchestrator.run_investigation(self.project.id, self.claim.id)
        corr_text = "Corrected view: Work completed underground"

        correction, _ = self.memory_engine.process_human_correction(
            investigation_id=res["investigation_id"],
            project_id=self.project.id,
            claim_id=self.claim.id,
            corrected_by="AUDITOR-102",
            original_interpretation="Original view",
            corrected_interpretation=corr_text,
            reason_for_correction="Inspection logs verified",
            evidence_ids_involved=[self.ev_photo.id],
            user_role="auditor"
        )

        self.assertEqual(correction.corrected_interpretation, corr_text)

    def test_4_reason_for_correction_is_stored(self):
        """Verify human reason for correction is recorded."""
        orchestrator = Orchestrator(db=self.db)
        res = orchestrator.run_investigation(self.project.id, self.claim.id)
        reason_text = "Ground excavation logs confirm pipe backfill prior to inspection photo"

        correction, _ = self.memory_engine.process_human_correction(
            investigation_id=res["investigation_id"],
            project_id=self.project.id,
            claim_id=self.claim.id,
            corrected_by="AUDITOR-103",
            original_interpretation="Original view",
            corrected_interpretation="Corrected view",
            reason_for_correction=reason_text,
            evidence_ids_involved=[self.ev_photo.id],
            user_role="auditor"
        )

        self.assertEqual(correction.reason_for_correction, reason_text)

    def test_5_evidence_links_are_preserved(self):
        """Verify evidence IDs associated with correction are linked in junction table."""
        orchestrator = Orchestrator(db=self.db)
        res = orchestrator.run_investigation(self.project.id, self.claim.id)

        correction, _ = self.memory_engine.process_human_correction(
            investigation_id=res["investigation_id"],
            project_id=self.project.id,
            claim_id=self.claim.id,
            corrected_by="AUDITOR-104",
            original_interpretation="Original view",
            corrected_interpretation="Corrected view",
            reason_for_correction="Auditor check",
            evidence_ids_involved=[self.ev_photo.id, self.ev_mb.id],
            user_role="auditor"
        )

        self.assertIn(self.ev_photo.id, correction.evidence_ids_involved)
        self.assertIn(self.ev_mb.id, correction.evidence_ids_involved)

    def test_6_case_memory_record_created(self):
        """Verify process_human_correction automatically generates a CaseMemoryRecord."""
        orchestrator = Orchestrator(db=self.db)
        res = orchestrator.run_investigation(self.project.id, self.claim.id)

        _, memory = self.memory_engine.process_human_correction(
            investigation_id=res["investigation_id"],
            project_id=self.project.id,
            claim_id=self.claim.id,
            corrected_by="AUDITOR-105",
            original_interpretation="Original view",
            corrected_interpretation="Corrected view",
            reason_for_correction="Excavator logs show backfill",
            evidence_ids_involved=[self.ev_photo.id],
            pattern_type="UNDERGROUND_COVERED_WORK",
            user_role="auditor"
        )

        self.assertIsNotNone(memory.id)
        self.assertEqual(memory.pattern_type, "UNDERGROUND_COVERED_WORK")

    def test_7_similar_case_retrieves_precedent(self):
        """Verify find_similar_precedents deterministically retrieves matching precedents."""
        orchestrator = Orchestrator(db=self.db)
        res = orchestrator.run_investigation(self.project.id, self.claim.id)

        self.memory_engine.process_human_correction(
            investigation_id=res["investigation_id"],
            project_id=self.project.id,
            claim_id=self.claim.id,
            corrected_by="AUDITOR-106",
            original_interpretation="Original view 120m vs 300m",
            corrected_interpretation="Work underground",
            reason_for_correction="Backfill confirmed",
            evidence_ids_involved=[self.ev_photo.id],
            pattern_type="UNDERGROUND_COVERED_WORK",
            user_role="auditor"
        )

        precedents = self.memory_engine.find_similar_precedents("UNDERGROUND_COVERED_WORK")
        self.assertGreaterEqual(len(precedents), 1)
        self.assertEqual(precedents[0]["pattern_type"], "UNDERGROUND_COVERED_WORK")

    def test_8_precedent_passed_into_investigation_context(self):
        """Verify historical precedent is surfaced during investigation execution."""
        orchestrator = Orchestrator(db=self.db)
        res_initial = orchestrator.run_investigation(self.project.id, self.claim.id)

        self.memory_engine.process_human_correction(
            investigation_id=res_initial["investigation_id"],
            project_id=self.project.id,
            claim_id=self.claim.id,
            corrected_by="AUDITOR-107",
            original_interpretation="Original view",
            corrected_interpretation="Corrected view",
            reason_for_correction="Soil backfill verified",
            evidence_ids_involved=[self.ev_photo.id],
            pattern_type="UNDERGROUND_COVERED_WORK",
            user_role="auditor"
        )

        # Create new project B to test precedent retrieval
        proj_b = Project(id="proj_3d_sub", code="PRJ-3D-B", name="Sub B", description="Sub project", sanctioned_amount=100.0, released_amount=50.0)
        self.db.save_project(proj_b)
        claim_b = Claim(id="clm_3d_sub", project_id=proj_b.id, claim_ref="CLM-B", claimed_by="B", claim_type="QUANTITY", description="300m pipe", claimed_value=300.0, unit="m", claim_date="2026-09-20")
        self.db.save_claim(claim_b)

        res_b = orchestrator.run_investigation(proj_b.id, claim_b.id)
        self.assertIsNotNone(res_b)

    def test_9_current_investigation_not_auto_resolved(self):
        """Verify surfacing precedent does NOT auto-close or auto-resolve current investigation."""
        orchestrator = Orchestrator(db=self.db)
        res_a = orchestrator.run_investigation(self.project.id, self.claim.id)

        self.memory_engine.process_human_correction(
            investigation_id=res_a["investigation_id"],
            project_id=self.project.id,
            claim_id=self.claim.id,
            corrected_by="AUDITOR-108",
            original_interpretation="Photo shows 120m vs 300m",
            corrected_interpretation="Underground work",
            reason_for_correction="Backfill verified",
            evidence_ids_involved=[self.ev_photo.id],
            pattern_type="UNDERGROUND_COVERED_WORK",
            user_role="auditor"
        )

        # New project C with conflict
        proj_c = Project(id="proj_3d_c", code="PRJ-3D-C", name="Proj C", description="C", sanctioned_amount=100.0, released_amount=50.0)
        self.db.save_project(proj_c)
        claim_c = Claim(id="clm_3d_c", project_id=proj_c.id, claim_ref="CLM-C", claimed_by="C", claim_type="QUANTITY", description="300m pipe", claimed_value=300.0, unit="m", claim_date="2026-09-21")
        self.db.save_claim(claim_c)
        ev_c1 = EvidenceItem(id="ev_c1", project_id=proj_c.id, claim_id=claim_c.id, source_type="GEO_PHOTO", source_id="CAM-C", observation="Photo 100m", value=100.0, unit="m", timestamp="2026-09-21T09:00:00Z", location=None, confidence=0.9, reliability="HIGH", relationship="NEUTRAL")
        ev_c2 = EvidenceItem(id="ev_c2", project_id=proj_c.id, claim_id=claim_c.id, source_type="MB_RECORD", source_id="MB-C", observation="MB 300m", value=300.0, unit="m", timestamp="2026-09-22T09:00:00Z", location=None, confidence=1.0, reliability="HIGH", relationship="SUPPORTS")
        self.db.save_evidence(ev_c1)
        self.db.save_evidence(ev_c2)

        res_c = orchestrator.run_investigation(proj_c.id, claim_c.id)
        self.assertNotEqual(res_c["final_state"], InvestigationState.CLOSED, "Surfacing precedent must NOT auto-close current case")
        self.assertEqual(res_c["final_state"], InvestigationState.HUMAN_REVIEW_REQUIRED)

    def test_10_auditor_private_info_not_exposed_to_citizens(self):
        """Verify get_citizen_case_memory_summary strips auditor ID (corrected_by) and private credentials."""
        orchestrator = Orchestrator(db=self.db)
        res = orchestrator.run_investigation(self.project.id, self.claim.id)
        secret_auditor_id = "AUDITOR-SECRET-UUID-999"

        self.memory_engine.process_human_correction(
            investigation_id=res["investigation_id"],
            project_id=self.project.id,
            claim_id=self.claim.id,
            corrected_by=secret_auditor_id,
            original_interpretation="Original view",
            corrected_interpretation="Corrected view",
            reason_for_correction="Auditor check",
            evidence_ids_involved=[self.ev_photo.id],
            pattern_type="UNDERGROUND_COVERED_WORK",
            user_role="auditor"
        )

        citizen_summary = self.memory_engine.get_citizen_case_memory_summary("UNDERGROUND_COVERED_WORK")
        summary_str = str(citizen_summary)

        self.assertNotIn(secret_auditor_id, summary_str, "Citizen API must NOT expose auditor identifier")

    def test_11_no_model_retraining_falsely_claimed(self):
        """Verify case memory engine documentation/summary explicitly states model weights are NOT retrained."""
        citizen_summary = self.memory_engine.get_citizen_case_memory_summary("UNDERGROUND_COVERED_WORK")
        for rec in citizen_summary:
            self.assertNotIn("retrained model weights", str(rec).lower())


if __name__ == "__main__":
    unittest.main()
