# SENTINEL PHASE 4A — REPRODUCIBLE VIDEO EVIDENCE CAPTURE REVIEW

**Status:** APPROVED & VERIFIED  
**Date:** September 26, 2026  
**Test Suite:** 84/84 PASSED  

---

## 1. EXECUTIVE SUMMARY

Phase 4A extends SENTINEL from single-image vision inference to **reproducible video evidence capture** ([`src/sentinel/vision/video_sampler.py`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/src/sentinel/vision/video_sampler.py)). It samples frames from local MP4 video files at configurable time intervals, extracts frame-level metadata and timestamps, reuses the existing pretrained `YOLODetector` pipeline, performs deterministic bounding-box deduplication, and normalizes frame observations into `NEUTRAL` Evidence Contracts.

---

## 2. ARCHITECTURAL PIPELINE

```
+--------------------+      +----------------------+      +----------------------+
| Local MP4 Video    | ---> | VideoFrameSampler    | ---> | Sampled Frame JPEGs  |
| File Path          |      | (1 frame / sec)      |      | + Frame Metadata     |
+--------------------+      +----------------------+      +----------------------+
                                                                     |
                                                                     v
+--------------------+      +----------------------+      +----------------------+
| Evidence Contract  | <--- | VisionEvidenceAdapter| <--- | YOLODetector         |
| (NEUTRAL Invariant)|      | (Perception-Only)    |      | (Reused yolov8n.pt)  |
+--------------------+      +----------------------+      +----------------------+
          |
          v
+--------------------+      +----------------------+
| VideoDeduplicator  | ---> | Compact Evidence     |
| (IoU >= 0.70)      |      | Timeline in DB       |
+--------------------+      +----------------------+
```

---

## 3. KEY ARCHITECTURAL INVARIANTS

### 1. Complete Frame Provenance
Every video evidence item retains complete trace provenance:
- `source_video`: Original video filename (e.g. `test_sentinel_site_video.mp4`).
- `frame_number`: Exact zero-indexed frame integer (`0`, `10`, `20`, ...).
- `frame_timestamp`: Calculated video time (`00:00:01.000`).
- `frame_dimensions`: Pixel dimensions (`640x480` or `1920x1080`).
- `model_checkpoint`: `yolov8n.pt`.

### 2. Timestamp Uncertainty Handling
- If video FPS is invalid, missing, or unparseable, `timestamp_uncertain` is set to `True` and timestamp defaults to `"TEMPORALLY_UNCERTAIN"`. Timestamps are **never** fabricated.

### 3. Perception-Only Intake
- Every extracted frame passes through `VisionEvidenceAdapter` producing `relationship = "NEUTRAL"`.
- Video observations do **not** directly convert repeated detections into `"construction completed"` or financial/fraud assertions.

### 4. Deterministic Frame Deduplication
- Bounding-box Intersection over Union (IoU) filtering ($\ge 0.70$ IoU within $3.0\text{ seconds}$) prevents generating hundreds of identical redundant evidence nodes for stationary objects across adjacent frames.

---

## 4. SAMPLE DEMO EXECUTION TIMELINE (`run_video_evidence_demo.py`)

```
===============================================================
 SENTINEL PHASE 4A — REPRODUCIBLE VIDEO EVIDENCE CAPTURE DEMO
===============================================================

[1] Generating sample site video file: C:\Users\Karthik\OneDrive\Desktop\sentinel\test_sentinel_site_video.mp4...
[2] Initializing VideoFrameSampler (1 frame / second)...
[2] Sampled 3 video frame(s):
  - Frame 0 (00:00:00.000): frame_000000.jpg
  - Frame 10 (00:00:01.000): frame_000010.jpg
  - Frame 20 (00:00:02.000): frame_000020.jpg

[3] Running YOLO inference over extracted frame images...
[4] Running VideoDeduplicator (IoU >= 0.70)...
Deduplicated 3 raw frame payloads into 1 unique perception items.

[5] Normalizing frame detections through VisionEvidenceAdapter...

===============================================================
 COMPACT VIDEO EVIDENCE TIMELINE
===============================================================
  Time [00:00:00.000] -> Source: VID-test_sentinel_site_video.mp4-FRM0 -> Rel: NEUTRAL | Observation: Pretrained Ultralytics YOLO model (yolov8n.pt) real image inference detected 1 bounding box(es)...

[SUCCESS] Invariant verified: All video frame evidence items are strictly NEUTRAL!
```

---

## 5. TEST SUITE VERIFICATION RESULT

```
python -m unittest discover -s tests -p "test_*.py" -v
----------------------------------------------------------------------
Ran 84 tests in 3.563s

OK
```

- **Phase 1A Tests:** 10/10 PASSED
- **Phase 1B Tests:** 10/10 PASSED
- **Phase 2A Tests:** 8/8 PASSED
- **Phase 2B.1 Tests:** 7/7 PASSED
- **Phase 3A Tests:** 7/7 PASSED
- **Phase 3A.1 Tests:** 5/5 PASSED
- **Phase 3B Tests:** 8/8 PASSED
- **Phase 3C Tests:** 10/10 PASSED
- **Phase 3D Tests:** 11/11 PASSED
- **Phase 4A Tests:** 8/8 PASSED
- **Total Suite:** 84/84 PASSED

---

## 6. PHASE 4A BOUNDARIES & STOPPING CONDITION

- **No Browser Webcam Implemented.**
- **No Continuous Live Streaming Implemented.**
- **No Complex Object Tracking Implemented.**
- **Phase 4A Complete. Stopping per instruction.**
