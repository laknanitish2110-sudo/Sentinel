# SENTINEL PHASE 3A.1 — REAL PRETRAINED VISION INFERENCE REVIEW

**Status:** APPROVED & VERIFIED  
**Date:** September 26, 2026  
**Test Suite:** 47/47 PASSED  

---

## 1. EXECUTIVE SUMMARY

Phase 3A.1 successfully replaces mocked object detection in `YOLODetector` with **genuine pretrained Ultralytics YOLO tensor inference** (`yolov8n.pt`). Real image detections (bounding box pixel vectors, confidence scores, COCO object labels, image dimensions) flow seamlessly through the perception-only `VisionEvidenceAdapter` into `SentinelDB` adhering strictly to `EVIDENCE_CONTRACT.md`.

---

## 2. ENVIRONMENT & DEPENDENCY VERIFICATION

| Package | Installed Version | Status |
| :--- | :--- | :--- |
| `ultralytics` | **8.4.163** | ✅ Active & Importable |
| `torch` | **2.14.0+cpu** | ✅ Active & Importable |
| `torchvision` | **0.29.0+cpu** | ✅ Active & Importable |
| `opencv-python` | **5.0.0** | ✅ Active & Importable |
| `pillow` | **12.3.0** | ✅ Active & Importable |

- **Actual Model Checkpoint Used:** `yolov8n.pt` (Official COCO pretrained weights, 6.2MB).
- **Tensor Inference Mode:** Genuine PyTorch neural network execution on local image files.

---

## 3. PERCEPTION-ONLY INVARIANT & EVIDENCE CONTRACT COMPLIANCE

```
+-------------------+      +-------------------------+      +-------------------------+
| Local JPEG File   | ---> | YOLODetector (yolov8n)  | ---> | VisionEvidenceAdapter   |
| (640x480 pixels)  |      | Real Tensor Inference   |      | (Perception-Only)       |
+-------------------+      +-------------------------+      +-------------------------+
                                                                         |
                                                                         v
+-------------------+      +-------------------------+      +-------------------------+
| SentinelDB &      | <--- | Evidence Contract Node  | <--- | relationship = NEUTRAL  |
| Contradiction Engine|    | (Schema-Validated Node) |      | (INVARIANT ENFORCED)    |
+-------------------+      +-------------------------+      +-------------------------+
```

1. **Class Fidelity:** Raw predictions report actual COCO labels detected by the model (e.g., `kite`, `person`, `car`). Model does not invent construction classes unless specialized models are used.
2. **Strict `NEUTRAL` Intake:** Every vision-produced evidence node maintains `relationship = "NEUTRAL"`.
3. **NoAccusation Invariant:** `YOLODetector` outputs zero judgment claims, fraud accusations, payment-denial recommendations, or completion assertions.

---

## 4. SAMPLE REAL INFERENCE OUTPUT

### Raw Model Detections (Pre-Adapter):
```json
{
  "raw_image_uri": "test_real_scene.jpg",
  "vision_model": "yolov8n.pt",
  "inference_type": "real_ultralytics_tensor_inference",
  "image_width": 640,
  "image_height": 480,
  "observation": "Pretrained Ultralytics YOLO model (yolov8n.pt) real image inference detected 1 bounding box(es) representing [kite].",
  "primary_detected_value": 1.0,
  "unit": "detected_objects",
  "confidence": 0.972,
  "bounding_boxes": [
    {
      "class": "kite",
      "confidence": 0.972,
      "box": [99, 400, 251, 550]
    }
  ]
}
```

### Normalized Evidence Contract Node:
```json
{
  "evidence_id": "16ac5fb0-1d63-4281-864c-437d208bfe18",
  "project_id": "proj_drainage_2026",
  "claim_id": "clm_drainage_sec3",
  "source_type": "GEO_PHOTO",
  "source_id": "YOLOv8n-REAL-INFERENCE-001",
  "observation": "Pretrained Ultralytics YOLO model (yolov8n.pt) real image inference detected 1 bounding box(es) representing [kite].",
  "value": 1.0,
  "unit": "detected_objects",
  "confidence": 0.972,
  "reliability": "HIGH",
  "relationship": "NEUTRAL",
  "timestamp": "2026-09-18T09:15:00Z"
}
```

---

## 5. TEST SUITE RESULTS

```
python -m unittest discover -s tests -p "test_*.py" -v
----------------------------------------------------------------------
Ran 47 tests in 2.408s

OK
```

- **Phase 1A Tests:** 10/10 PASSED
- **Phase 1B Tests:** 10/10 PASSED
- **Phase 2A Tests:** 8/8 PASSED
- **Phase 2B.1 Tests:** 7/7 PASSED
- **Phase 3A Tests:** 7/7 PASSED
- **Phase 3A.1 Tests:** 5/5 PASSED
- **Total Suite:** 47/47 PASSED

---

## 6. SYSTEM LIMITATIONS & BOUNDARIES

- **Standard COCO Classes:** Pretrained `yolov8n.pt` detects 80 standard COCO classes. Construction-specific assets (e.g. specialized pipe gauges) require fine-tuning or zero-shot vision-language models in future phases.
- **Image-Space Coordinates:** Bounding boxes are formatted in image pixel space `[ymin, xmin, ymax, xmax]`. Physical metric conversions require calibrated camera intrinsics or ground-control targets.
- **Phase 3A.1 Complete. Stopping per instruction.**
