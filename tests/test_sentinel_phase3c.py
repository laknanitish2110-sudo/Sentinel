"""
SENTINEL Phase 3C Test Suite — Evidence-Aware Spatial and Temporal Reasoning.
Verifies spatial proximity calculation, chronological ordering, missing metadata handling,
provenance preservation, perception-only bounds, and integration with ContradictionEngine.
"""
import unittest
from sentinel.types import EvidenceItem
from sentinel.engines.spatial_temporal_engine import SpatialTemporalEngine
from sentinel.engines.contradiction_engine import ContradictionEngine


class TestSentinelPhase3C(unittest.TestCase):

    def setUp(self):
        self.st_engine = SpatialTemporalEngine(spatial_threshold_km=0.50)

        # Sample co-located site inspection photo (Location L1: 12.9720, 77.5950)
        self.ev_photo_l1 = EvidenceItem(
            id="ev_photo_l1",
            project_id="proj_3c_demo",
            claim_id="clm_3c_01",
            source_type="GEO_PHOTO",
            source_id="CAM-001",
            observation="Photo showing trench excavation with laid RCC pipe",
            value=180.0,
            unit="meters",
            timestamp="2026-09-15T09:00:00Z",
            location={"latitude": 12.9720, "longitude": 77.5950, "address": "Ward 7 Drain Site"},
            confidence=0.92,
            reliability="HIGH",
            relationship="NEUTRAL"
        )

        # Sample co-located MB record at same location L1, timestamp 3 days later
        self.ev_mb_l1 = EvidenceItem(
            id="ev_mb_l1",
            project_id="proj_3c_demo",
            claim_id="clm_3c_01",
            source_type="MB_RECORD",
            source_id="MB-402",
            observation="Measurement book entry certifying 400m pipe completed",
            value=400.0,
            unit="meters",
            timestamp="2026-09-18T10:00:00Z",
            location={"latitude": 12.9722, "longitude": 77.5951, "address": "Ward 7 Drain Site"},
            confidence=1.0,
            reliability="HIGH",
            relationship="SUPPORTS"
        )

        # Sample distant photo at Location L2 (~15 km away)
        self.ev_photo_l2 = EvidenceItem(
            id="ev_photo_l2",
            project_id="proj_3c_demo",
            claim_id="clm_3c_01",
            source_type="GEO_PHOTO",
            source_id="CAM-002",
            observation="Site photo taken at different ward location",
            value=180.0,
            unit="meters",
            timestamp="2026-09-15T09:00:00Z",
            location={"latitude": 13.0827, "longitude": 80.2707, "address": "Ward 12 Site"},
            confidence=0.90,
            reliability="MEDIUM",
            relationship="NEUTRAL"
        )

        # Sample evidence with missing location (no GPS)
        self.ev_missing_loc = EvidenceItem(
            id="ev_no_loc",
            project_id="proj_3c_demo",
            claim_id="clm_3c_01",
            source_type="DOCUMENT",
            source_id="DOC-99",
            observation="Unlocated paper invoice",
            value=180.0,
            unit="meters",
            timestamp="2026-09-15T09:00:00Z",
            location=None,
            confidence=0.70,
            reliability="MEDIUM",
            relationship="NEUTRAL"
        )

        # Sample evidence with missing timestamp
        self.ev_missing_ts = EvidenceItem(
            id="ev_no_ts",
            project_id="proj_3c_demo",
            claim_id="clm_3c_01",
            source_type="GEO_PHOTO",
            source_id="CAM-003",
            observation="Photo without timestamp metadata",
            value=180.0,
            unit="meters",
            timestamp=None,
            location={"latitude": 12.9720, "longitude": 77.5950},
            confidence=0.85,
            reliability="MEDIUM",
            relationship="NEUTRAL"
        )

    def test_1_same_location_evidence_identified_as_spatially_relevant(self):
        """Verify evidence items within threshold distance (e.g. <500m) are marked SPATIALLY_RELEVANT."""
        rel, dist_km = self.st_engine.evaluate_spatial_proximity(
            self.ev_photo_l1.location, self.ev_mb_l1.location
        )
        self.assertEqual(rel, "SPATIALLY_RELEVANT")
        self.assertIsNotNone(dist_km)
        self.assertLessEqual(dist_km, 0.50)

    def test_2_different_locations_not_treated_as_equivalent(self):
        """Verify evidence items at distant locations (~15km+) are marked SPATIALLY_DISTANT."""
        rel, dist_km = self.st_engine.evaluate_spatial_proximity(
            self.ev_photo_l1.location, self.ev_photo_l2.location
        )
        self.assertEqual(rel, "SPATIALLY_DISTANT")
        self.assertGreater(dist_km, 10.0)

    def test_3_missing_gps_does_not_produce_guessed_coordinates(self):
        """Verify missing GPS metadata yields SPATIALLY_UNCERTAIN without fabricating coordinates."""
        rel, dist_km = self.st_engine.evaluate_spatial_proximity(
            self.ev_photo_l1.location, self.ev_missing_loc.location
        )
        self.assertEqual(rel, "SPATIALLY_UNCERTAIN")
        self.assertIsNone(dist_km)

    def test_4_chronological_ordering_works(self):
        """Verify chronological order detects BEFORE, AFTER, and project period alignment."""
        rel, delta_sec = self.st_engine.evaluate_temporal_relationship(
            self.ev_photo_l1.timestamp, self.ev_mb_l1.timestamp
        )
        self.assertEqual(rel, "EVIDENCE_BEFORE_RECORD")
        self.assertGreater(delta_sec, 0)

        # Project period check
        period_rel = self.st_engine.evaluate_project_period_alignment(
            self.ev_photo_l1.timestamp,
            start_date="2026-09-01T00:00:00Z",
            end_date="2026-09-30T00:00:00Z"
        )
        self.assertEqual(period_rel, "EVIDENCE_WITHIN_PROJECT_PERIOD")

    def test_5_missing_timestamps_represented_as_uncertain(self):
        """Verify missing timestamp yields TEMPORALLY_UNCERTAIN."""
        rel, delta_sec = self.st_engine.evaluate_temporal_relationship(
            self.ev_photo_l1.timestamp, self.ev_missing_ts.timestamp
        )
        self.assertEqual(rel, "TEMPORALLY_UNCERTAIN")
        self.assertIsNone(delta_sec)

    def test_6_evidence_provenance_is_preserved(self):
        """Verify context evaluation output preserves source evidence IDs and metadata."""
        context = self.st_engine.evaluate_context(self.ev_photo_l1, self.ev_mb_l1)
        self.assertEqual(context["evidence_a_id"], self.ev_photo_l1.id)
        self.assertEqual(context["evidence_b_id"], self.ev_mb_l1.id)
        self.assertIn("spatial_relationship", context)
        self.assertIn("temporal_relationship", context)

    def test_7_spatial_temporal_relevance_does_not_become_supports(self):
        """Verify spatial/temporal co-location does NOT override evidence to SUPPORTS."""
        context = self.st_engine.evaluate_context(self.ev_photo_l1, self.ev_photo_l2)
        self.assertIsNone(context["relationship_override"])
        self.assertNotEqual(context["contextual_relevance"], "SUPPORTS")

    def test_8_spatial_temporal_relevance_does_not_become_contradicts(self):
        """Verify spatial/temporal co-location does NOT override evidence to CONTRADICTS."""
        context = self.st_engine.evaluate_context(self.ev_photo_l1, self.ev_mb_l1)
        self.assertIsNone(context["relationship_override"])
        self.assertNotEqual(context["contextual_relevance"], "CONTRADICTS")

    def test_9_no_fraud_or_judgment_terms_emitted(self):
        """Verify engine raises ValueError if any forbidden financial/legal/fraud judgment term is emitted."""
        with self.assertRaises(ValueError):
            self.st_engine._validate_safety_invariants("Evidence demonstrates FRAUDULENT activity")

    def test_10_contradiction_engine_integrates_spatial_temporal_context(self):
        """Verify ContradictionEngine attaches spatial/temporal context metadata to contradiction records."""
        c_engine = ContradictionEngine(spatial_temporal_engine=self.st_engine)
        contradictions = c_engine.evaluate_contradictions(
            investigation_id="inv_3c_01",
            project_id="proj_3c_demo",
            claim_id="clm_3c_01",
            evidence_items=[self.ev_photo_l1, self.ev_mb_l1]
        )

        self.assertEqual(len(contradictions), 1)
        c_record = contradictions[0]
        self.assertIn("spatial_temporal_context", c_record.metadata)
        st_meta = c_record.metadata["spatial_temporal_context"]
        self.assertEqual(st_meta["spatial_relationship"], "SPATIALLY_RELEVANT")
        self.assertEqual(st_meta["temporal_relationship"], "EVIDENCE_BEFORE_RECORD")


if __name__ == "__main__":
    unittest.main()
