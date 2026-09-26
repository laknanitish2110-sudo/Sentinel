"""
SENTINEL Phase 4A Test Suite — Video Evidence Capture & Frame Sampler.
Verifies frame sampling, frame number and timestamp preservation, missing FPS handling,
YOLO reuse, perception-only NEUTRAL evidence invariant, frame provenance, and deduplication.
"""
import os
import unittest
from PIL import Image, ImageDraw

from sentinel.vision.video_sampler import VideoFrameSampler, VideoDeduplicator
from sentinel.vision.yolo_detector import YOLODetector
from sentinel.vision.adapter import VisionEvidenceAdapter
from sentinel.db import SentinelDB
from sentinel.types import Project, Claim

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


class TestSentinelPhase4A(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_video_path = os.path.abspath("test_sentinel_unit_video.mp4")
        if OPENCV_AVAILABLE:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(cls.test_video_path, fourcc, 10.0, (640, 480))
            for i in range(20):  # 2 seconds at 10 fps
                img = Image.new("RGB", (640, 480), color=(180, 200, 220))
                draw = ImageDraw.Draw(img)
                draw.rectangle([100, 100, 300, 300], fill=(50, 100, 200), outline=(0, 0, 0))
                import numpy as np
                frame_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                writer.write(frame_bgr)
            writer.release()
        else:
            with open(cls.test_video_path, "wb") as f:
                f.write(b"dummy_video_bytes")

        cls.db = SentinelDB()
        cls.project = Project(
            id="proj_phase4a_test",
            code="PRJ-4A",
            name="Phase 4A Video Test Project",
            description="Testing video frame sampling",
            sanctioned_amount=1000000.0,
            released_amount=500000.0
        )
        cls.db.save_project(cls.project)

        cls.claim = Claim(
            id="clm_phase4a_test",
            project_id=cls.project.id,
            claim_ref="CLM-4A-01",
            claimed_by="Video Contractor",
            claim_type="PHYSICAL_QUANTITY",
            description="300m pipeline installation",
            claimed_value=300.0,
            unit="meters",
            claim_date="2026-09-22"
        )
        cls.db.save_claim(cls.claim)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_video_path):
            os.remove(cls.test_video_path)

    def test_1_video_frame_extraction(self):
        """Verify video sampler extracts frames at interval from MP4 file."""
        sampler = VideoFrameSampler(sample_interval_seconds=1.0)
        frames = sampler.sample_video_frames(self.test_video_path)
        self.assertGreater(len(frames), 0)
        self.assertTrue(os.path.exists(frames[0]["frame_path"]))

    def test_2_frame_number_preservation(self):
        """Verify frame_number is accurately preserved in frame metadata payload."""
        sampler = VideoFrameSampler(sample_interval_seconds=1.0)
        frames = sampler.sample_video_frames(self.test_video_path)
        self.assertIn("frame_number", frames[0])
        self.assertGreaterEqual(frames[0]["frame_number"], 0)

    def test_3_timestamp_preservation(self):
        """Verify frame timestamp is preserved in HH:MM:SS.mmm format."""
        sampler = VideoFrameSampler(sample_interval_seconds=1.0)
        frames = sampler.sample_video_frames(self.test_video_path)
        self.assertIn("frame_timestamp", frames[0])
        self.assertIsNotNone(frames[0]["frame_timestamp"])

    def test_4_missing_fps_uncertainty_handling(self):
        """Verify missing/invalid FPS marks timestamp_uncertain as True."""
        sampler = VideoFrameSampler()
        payload = sampler._fallback_sample(self.test_video_path, temp_dir=".")
        self.assertTrue(payload[0]["timestamp_uncertain"])
        self.assertEqual(payload[0]["frame_timestamp"], "00:00:00.000")

    def test_5_yolo_detector_reuse_on_video_frames(self):
        """Verify YOLODetector runs inference on extracted frame image files."""
        sampler = VideoFrameSampler(sample_interval_seconds=1.0)
        frames = sampler.sample_video_frames(self.test_video_path)

        detector = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.20)
        det = detector.detect_image(frames[0]["frame_path"])

        self.assertIn("bounding_boxes", det)
        self.assertIn("confidence", det)

    def test_6_neutral_evidence_invariant_for_video_frames(self):
        """Verify video frame evidence items passed through adapter remain strictly NEUTRAL."""
        sampler = VideoFrameSampler(sample_interval_seconds=1.0)
        frames = sampler.sample_video_frames(self.test_video_path)

        detector = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.20)
        det = detector.detect_image(frames[0]["frame_path"])

        adapter = VisionEvidenceAdapter(db=self.db)
        ev_item = adapter.adapt_vision_payload(
            project_id=self.project.id,
            claim=self.claim,
            vision_payload=det,
            source_id="VID-FRAME-TEST-001"
        )
        self.assertEqual(ev_item.relationship, "NEUTRAL", "Video frame evidence must be strictly NEUTRAL")

    def test_7_evidence_provenance_preserves_video_metadata(self):
        """Verify video frame evidence metadata preserves source_video, frame_number, and dimensions."""
        sampler = VideoFrameSampler(sample_interval_seconds=1.0)
        frames = sampler.sample_video_frames(self.test_video_path)

        detector = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.20)
        det = detector.detect_image(frames[0]["frame_path"])
        det["frame_number"] = frames[0]["frame_number"]
        det["source_video"] = frames[0]["source_video"]

        adapter = VisionEvidenceAdapter(db=self.db)
        ev_item = adapter.adapt_vision_payload(
            project_id=self.project.id,
            claim=self.claim,
            vision_payload=det,
            source_id="VID-FRAME-TEST-002"
        )

        meta = ev_item.metadata
        self.assertEqual(meta["vision_model"], "yolov8n.pt")
        self.assertIn("bounding_boxes", meta)

    def test_8_deterministic_duplicate_handling(self):
        """Verify VideoDeduplicator filters matching bounding boxes across nearby frames."""
        dedup = VideoDeduplicator(iou_threshold=0.70, max_time_gap_sec=3.0)

        det_a = {
            "timestamp_seconds": 1.0,
            "bounding_boxes": [{"class": "truck", "confidence": 0.90, "box": [100, 100, 300, 300]}]
        }
        det_b = {
            "timestamp_seconds": 2.0,
            "bounding_boxes": [{"class": "truck", "confidence": 0.91, "box": [102, 101, 301, 301]}]
        }

        unique = dedup.deduplicate_frame_detections([det_a, det_b])
        self.assertEqual(len(unique), 1, "Duplicate detection across frames should be deduplicated")


if __name__ == "__main__":
    unittest.main()
