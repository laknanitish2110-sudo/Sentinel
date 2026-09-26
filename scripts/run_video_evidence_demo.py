"""
SENTINEL Phase 4A Demo — Video Evidence Capture & Timeline Processing.

Demonstrates:
1. Video Frame Sampler extracting timestamped frames from local MP4 video.
2. Real Ultralytics YOLO inference across extracted frame images.
3. Provenance preservation (frame_number, video_source, frame_timestamp).
4. VisionEvidenceAdapter normalization to NEUTRAL Evidence Contract.
5. Deterministic video frame deduplication.
6. Compact chronological video evidence timeline printing.
"""
import os
import sys
import tempfile
from PIL import Image, ImageDraw

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sentinel.vision.video_sampler import VideoFrameSampler, VideoDeduplicator
from sentinel.vision.yolo_detector import YOLODetector, ULTRALYTICS_AVAILABLE
from sentinel.vision.adapter import VisionEvidenceAdapter
from sentinel.db import SentinelDB
from sentinel.types import Project, Claim


def create_sample_mp4_video(output_path: str, duration_sec: int = 3, fps: int = 10) -> str:
    """Generates a synthetic MP4 video for local demonstration."""
    if not OPENCV_AVAILABLE:
        # If OpenCV VideoWriter unavailable, create dummy file
        with open(output_path, "wb") as f:
            f.write(b"dummy_video_bytes")
        return output_path

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, float(fps), (640, 480))

    total_frames = duration_sec * fps
    for i in range(total_frames):
        # Create a frame image with moving shapes
        img = Image.new("RGB", (640, 480), color=(180, 200, 220))
        draw = ImageDraw.Draw(img)
        # Move rectangle across frame
        x_offset = int((i / total_frames) * 300)
        draw.rectangle([50 + x_offset, 100, 200 + x_offset, 300], fill=(50, 100, 200), outline=(0, 0, 0))
        draw.ellipse([350, 150, 450, 250], fill=(200, 50, 50), outline=(0, 0, 0))

        # Convert PIL to cv2 BGR numpy array
        import numpy as np
        frame_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        writer.write(frame_bgr)

    writer.release()
    return output_path


def main():
    print("===============================================================")
    print(" SENTINEL PHASE 4A — REPRODUCIBLE VIDEO EVIDENCE CAPTURE DEMO")
    print("===============================================================\n")

    # 1. Create synthetic video file
    video_path = os.path.abspath("test_sentinel_site_video.mp4")
    print(f"[1] Generating sample site video file: {video_path}...")
    create_sample_mp4_video(video_path, duration_sec=3, fps=10)

    # 2. Sample video frames
    print("[2] Initializing VideoFrameSampler (1 frame / second)...")
    sampler = VideoFrameSampler(sample_interval_seconds=1.0)
    sampled_frames = sampler.sample_video_frames(video_path)

    print(f"[2] Sampled {len(sampled_frames)} video frame(s):")
    for frame in sampled_frames:
        print(f"  - Frame {frame['frame_number']} ({frame['frame_timestamp']}): {frame['frame_path']}")

    # 3. Instantiate YOLODetector and run inference over frames
    print("\n[3] Running YOLO inference over extracted frame images...")
    detector = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.20)
    
    frame_detections = []
    for frame in sampled_frames:
        detection = detector.detect_image(
            frame["frame_path"],
            location_override={"latitude": 12.9716, "longitude": 77.5946, "address": "Drainage Site Camera 01"}
        )
        # Attach frame metadata
        detection["frame_number"] = frame["frame_number"]
        detection["frame_timestamp"] = frame["frame_timestamp"]
        detection["timestamp_seconds"] = frame["timestamp_seconds"]
        detection["source_video"] = frame["source_video"]
        frame_detections.append(detection)

    # 4. Perform deterministic frame deduplication
    print("\n[4] Running VideoDeduplicator (IoU >= 0.70)...")
    dedup = VideoDeduplicator(iou_threshold=0.70)
    unique_detections = dedup.deduplicate_frame_detections(frame_detections)
    print(f"Deduplicated {len(frame_detections)} raw frame payloads into {len(unique_detections)} unique perception items.")

    # 5. Initialize DB and seed parent records for FK integrity
    db = SentinelDB()
    project = Project(
        id="proj_video_demo",
        code="PRJ-VID-001",
        name="Ward 12 Video Evidence Project",
        description="Video-based site monitoring",
        sanctioned_amount=4000000.0,
        released_amount=2000000.0
    )
    db.save_project(project)

    claim = Claim(
        id="clm_video_demo",
        project_id=project.id,
        claim_ref="CLM-VID-01",
        claimed_by="Contractor Vid",
        claim_type="PHYSICAL_QUANTITY",
        description="Drain excavation and pipeline installation",
        claimed_value=300.0,
        unit="meters",
        claim_date="2026-09-22"
    )
    db.save_claim(claim)

    # 6. Normalize via VisionEvidenceAdapter
    print("\n[5] Normalizing frame detections through VisionEvidenceAdapter...")
    adapter = VisionEvidenceAdapter(db=db)
    persisted_items = []

    for det in unique_detections:
        ev_item = adapter.adapt_vision_payload(
            project_id=project.id,
            claim=claim,
            vision_payload=det,
            source_id=f"VID-{det['source_video']}-FRM{det['frame_number']}"
        )
        persisted_items.append(ev_item)

    # 7. Print Video Evidence Timeline
    print("\n===============================================================")
    print(" COMPACT VIDEO EVIDENCE TIMELINE")
    print("===============================================================")
    for item in persisted_items:
        meta = item.metadata or {}
        frm_ts = meta.get("frame_timestamp") or item.timestamp
        print(f"  Time [{frm_ts}] -> Source: {item.source_id} -> Rel: {item.relationship} | Observation: {item.observation[:80]}...")

    # 8. Verify perception-only invariant
    all_neutral = all(i.relationship == "NEUTRAL" for i in persisted_items)
    if all_neutral:
        print("\n[SUCCESS] Invariant verified: All video frame evidence items are strictly NEUTRAL!")
    else:
        print("\n[FAILURE] Perception invariant violated!")
        sys.exit(1)

    # Cleanup synthetic video file
    if os.path.exists(video_path):
        os.remove(video_path)

    print("\n===============================================================")
    print(" DEMO COMPLETE — VIDEO EVIDENCE CAPTURE INTEGRATED SUCCESSFULLY")
    print("===============================================================")


if __name__ == "__main__":
    main()
