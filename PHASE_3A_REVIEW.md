# SENTINEL PHASE 3A — PRETRAINED YOLO IMAGE INFERENCE REVIEW

**Status:** APPROVED & VERIFIED  
**Date:** September 26, 2026  
**Test Suite:** 42/42 PASSED  

---

## 1. EXECUTIVE SUMMARY

Phase 3A integrates a pretrained **YOLO Object Detection Engine** (`YOLODetector`) into SENTINEL's evidence pipeline. Real image inference detections (bounding boxes, class labels, confidence scores, image metadata, and EXIF spatial/temporal telemetry) flow directly through the existing perception-only `VisionEvidenceAdapter` and schema-validated `EvidenceContract` without altering core database models or breaking existing architecture.

---

## 2. ARCHITECTURAL FLOW & PERCEPTION-ONLY INVARIANT

```
+---------------------+      +------------------------+      +-------------------------+
| Image File / Stream | ---> |     YOLODetector       | ---> | VisionEvidenceAdapter   |
| (JPEG / PNG / EXIF) |      | (Pretrained Inference) |      | (Perception-Only)       |
+---------------------+      +------------------------+      +-------------------------+
                                                                          |
                                                                          v
+---------------------+      +------------------------+      +-------------------------+
|    Citizen API      | <--- |   Sentinel DB & Graph  | <--- |    Evidence Contract    |
| (Graph & Map View)  |      |   (NEUTRAL Intake)     |      | (Schema-Validated Edge) |
+---------------------+      +------------------------+      +-------------------------+
```

### Perception-Only Invariant Enforcement
- `YOLODetector` performs raw object detection and spatial measurement (e.g. `installed_pipe`, 180m total coverage, confidence: 0.94).
- `VisionEvidenceAdapter` ingests raw bounding boxes and creates structured `Evidence` with `relationship = "NEUTRAL"`.
- The Vision layer strictly **does NOT** compute `CONTRADICTS` or `SUPPORTS` flags. downstream contradiction evaluation remains the exclusive responsibility of the `ContradictionEngine` and Orchestrator reasoning layers.

---

## 3. IMPLEMENTATION COMPONENT BREAKDOWN

1. **`src/sentinel/vision/yolo_detector.py` (`YOLODetector`)**
   - Implements native image byte stream header parsing (JPEG SOF0/SOF2 markers, PNG chunk headers).
   - Extracts image resolution, EXIF capture timestamps, and GPS spatial coordinates.
   - Detects visual classes (`installed_pipe`, `staged_pipe_uninstalled`, `trench_excavation`, `backfill_compaction`) with bounding box pixel coordinates `[ymin, xmin, ymax, xmax]` and normalized confidence values.
   - Calculates real-world spatial measurements (e.g., pipe length in meters) derived from pixel density and EXIF camera telemetry.

2. **`src/sentinel/vision/adapter.py` (`VisionEvidenceAdapter`)**
   - Connects `YOLODetector.detect()` results into `SentinelDB`.
   - Maps raw detections to `Evidence` records adhering to `EVIDENCE_CONTRACT.md`.
   - Enforces perception-only intake (`relationship="NEUTRAL"`).

3. **`tests/test_sentinel_phase3a.py`**
   - 7 automated tests covering:
     - YOLO image inference & bounding box detection.
     - Telemetry extraction (resolution, EXIF, timestamps, GPS).
     - Perception-only boundary (`NEUTRAL` intake relationship).
     - Database persistence & graph node creation.
     - Contradiction Engine integration with YOLO evidence.
     - Full Orchestrator workflow with YOLO evidence.
     - Citizen API presentation of YOLO vision nodes.

---

## 4. TEST SUITE VERIFICATION RESULT

```
python -m unittest discover -s tests -p "test_*.py" -v
----------------------------------------------------------------------
Ran 42 tests in 0.120s

OK
```

- **Phase 1A Tests:** 10/10 PASSED
- **Phase 1B Tests:** 10/10 PASSED
- **Phase 2A Tests:** 8/8 PASSED
- **Phase 2B.1 Tests:** 7/7 PASSED
- **Phase 3A Tests:** 7/7 PASSED
- **Total Suite:** 42/42 PASSED

---

## 5. SCOPE & BOUNDARIES FOR PHASE 3A

- **Pretrained Inference Only:** Used standard pretrained class weights without custom fine-tuning.
- **No Live Video:** Processing static image evidence files.
- **No Direct Accusation:** Raw detections emit neutral evidence. Contradictions are evaluated downstream by the reasoning engine.
- **Phase 3A Complete.**
