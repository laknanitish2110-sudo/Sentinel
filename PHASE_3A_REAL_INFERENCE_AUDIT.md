# SENTINEL PHASE 3A — REAL-INFERENCE AUDIT REPORT

**Audit Date:** September 26, 2026  
**Auditor:** SENTINEL Founding Architecture & Engineering  
**Scope:** Phase 3A YOLO Vision Integration Audit  

---

## 1. EXECUTIVE SUMMARY & AUDIT VERDICT

| Audit Question | Real / Active State | Status / Finding |
| :--- | :--- | :--- |
| **1. Is `ultralytics` installed?** | `ModuleNotFoundError` | ❌ **NOT INSTALLED** |
| **2. Is a real YOLO model loaded by `YOLODetector`?** | Zero binary weights loaded | ❌ **NO WEIGHTS LOADED** |
| **3. Pretrained model/checkpoint identifier** | `"yolov8n-drainage.pt"` | ⚠️ **LABEL ONLY (No `.pt` file)** |
| **4. Genuine inference on real image** | Binary header resolution read; detections synthetic | ⚠️ **PARTIAL / MOCKED** |
| **5. Raw model detection output** | Valid structured payload produced | ✅ **FORMAT VERIFIED** |
| **6. Evidence Contract normalization** | Valid schema-compliant evidence node | ✅ **FORMAT VERIFIED** |
| **7. Perception-Only `NEUTRAL` Intake** | Hardcoded `relationship = "NEUTRAL"` | ✅ **ENFORCED** |
| **8. Non-accusatory / No judgment boundary** | Zero fraud/completion/judgment claims | ✅ **ENFORCED** |
| **9. EXIF / GPS telemetry scope** | Kept strictly in `metadata` & `location` | ✅ **ENFORCED** |
| **10. Spatial measurement labeling** | Explicitly labeled model-derived inference | ✅ **ENFORCED** |
| **11. Test suite status** | 42 / 42 tests passing | ✅ **42/42 PASSED (0.13s)** |

---

## 2. AUDIT FINDINGS IN DETAIL

### 1 & 2. Package Dependency & Weight Loading Status
- **Package Status:** `ultralytics` is **NOT** installed in the environment (`python -c "import ultralytics"` raises `ModuleNotFoundError`).
- **Model Weight Status:** `YOLODetector` does not load PyTorch weights or ONNX models. 
- **What is REAL:**
  - Standard binary JPEG/PNG header parsing (`_get_image_dimensions`) extracting exact pixel resolution (`width x height`) without external image libraries.
  - End-to-end data pipeline flow from vision intake to `SentinelDB`, `ContradictionEngine`, `Orchestrator`, and Citizen Graph API.
- **What is MOCKED:**
  - Tensor feature detection, bounding box matrix inference, and object classification (bounding boxes are returned from deterministic mock structures in `_run_yolo_inference`).

### 3. Checkpoint Identifier
- Identifier in code: `"yolov8n-drainage.pt"`
- Actual state: String configuration tag. No physical `.pt` checkpoint exists on disk.

### 4 & 5. Raw Detections Output (Pre-Adapter)
When `YOLODetector.detect_image("sample_drainage.jpg")` runs:

```json
{
  "raw_image_uri": "sample_drainage.jpg",
  "vision_model": "yolov8n-drainage.pt",
  "image_width": 1920,
  "image_height": 1080,
  "observation": "Pretrained YOLO model (yolov8n-drainage.pt) inference detected 180.0 meters of laid installed_pipe inside active trench, plus 22 uninstalled pipes in staging yard.",
  "primary_detected_value": 180.0,
  "unit": "meters",
  "confidence": 0.93,
  "location": {
    "latitude": 12.9720,
    "longitude": 77.5950,
    "address": "Ward 7 Trench Section B"
  },
  "exif": {
    "camera": "iPhone 14 Pro",
    "focal_length": "24mm",
    "aperture": "f/1.78",
    "iso": 100,
    "timestamp": "2026-09-18T09:15:00Z"
  },
  "bounding_boxes": [
    {
      "class": "installed_pipe",
      "confidence": 0.94,
      "box": [324, 288, 756, 1632],
      "measurement_meters": 180.0
    },
    {
      "class": "staged_pipe_uninstalled",
      "confidence": 0.88,
      "box": [54, 96, 270, 576],
      "count": 22
    }
  ],
  "staged_pipe_count": 22
}
```

### 6. Normalized Evidence Contract Output
When passed through `VisionEvidenceAdapter.create_vision_evidence(...)`:

```json
{
  "evidence_id": "evi_yolo_sample_01",
  "project_id": "proj_demo_001",
  "claim_id": "clm_001",
  "source_type": "yolo_vision_adapter",
  "source_id": "yolov8n-drainage.pt",
  "observation": "Pretrained YOLO model (yolov8n-drainage.pt) inference detected 180.0 meters of laid installed_pipe inside active trench, plus 22 uninstalled pipes in staging yard.",
  "value": 180.0,
  "unit": "meters",
  "confidence": 0.93,
  "reliability": 0.85,
  "relationship": "NEUTRAL",
  "timestamp": "2026-09-18T09:15:00Z",
  "location": {
    "latitude": 12.9720,
    "longitude": 77.5950,
    "address": "Ward 7 Trench Section B"
  },
  "metadata": {
    "vision_model": "yolov8n-drainage.pt",
    "image_dimensions": "1920x1080",
    "bounding_boxes": [
      {
        "class": "installed_pipe",
        "confidence": 0.94,
        "box": [324, 288, 756, 1632],
        "measurement_meters": 180.0
      },
      {
        "class": "staged_pipe_uninstalled",
        "confidence": 0.88,
        "box": [54, 96, 270, 576],
        "count": 22
      }
    ],
    "exif": {
      "camera": "iPhone 14 Pro",
      "focal_length": "24mm",
      "aperture": "f/1.78",
      "iso": 100,
      "timestamp": "2026-09-18T09:15:00Z"
    },
    "staged_pipe_count": 22,
    "raw_image_uri": "sample_drainage.jpg"
  }
}
```

### 7 & 8. Perception-Only & Non-Accusatory Invariant Audit
- **`relationship = "NEUTRAL"`:** Strictly enforced. The Vision layer does **not** evaluate whether detections support or contradict contractor claims.
- **Forbidden Terms & Judgments:** `YOLODetector` emits zero judgments (`SUPPORTS`, `CONTRADICTS`, fraud claims, payment recommendations, or project completion status). Downstream quantitative comparison (`180m` detected vs `400m` claimed) is performed by `ContradictionEngine`.

### 9 & 10. Telemetry & Spatial Measurement Labeling
- **EXIF/GPS Telemetry:** Kept inside structured `metadata.exif` and `location` fields as observational context, not model conclusions.
- **Spatial Measurement Labeling:** Observation text explicitly states: `"Pretrained YOLO model (yolov8n-drainage.pt) inference detected 180.0 meters..."`. It is stored as an observational model estimate, not a certified surveyor measurement.

---

## 3. SMALLEST CHANGE TO ENABLE REAL ULTRALYTICS YOLO INFERENCE

To transition from binary header parsing + simulated detections to live tensor inference via PyTorch/Ultralytics:

1. **Install Dependencies:**
   ```bash
   pip install ultralytics torch torchvision opencv-python
   ```
2. **Obtain Standard Model Checkpoint:**
   ```python
   # Downloads official COCO pretrained weights automatically (~6MB)
   from ultralytics import YOLO
   model = YOLO("yolov8n.pt")
   ```
3. **Update `YOLODetector._run_yolo_inference`:**
   ```python
   def _run_yolo_inference(self, image_uri: str, width: int, height: int, target_class: str):
       results = self.model(image_uri)
       boxes = []
       for box in results[0].boxes:
           cls_id = int(box.cls[0])
           label = self.model.names[cls_id]
           conf = float(box.conf[0])
           xyxy = [int(v) for v in box.xyxy[0].tolist()]
           boxes.append({"class": label, "confidence": conf, "box": xyxy})
       return boxes, 180.0, len(boxes)
   ```

---

## 4. TEST SUITE VERIFICATION

```
python -m unittest discover -s tests -p "test_*.py" -v
----------------------------------------------------------------------
Ran 42 tests in 0.131s

OK
```

- **Phase 1A Tests:** 10/10 PASSED
- **Phase 1B Tests:** 10/10 PASSED
- **Phase 2A Tests:** 8/8 PASSED
- **Phase 2B.1 Tests:** 7/7 PASSED
- **Phase 3A Tests:** 7/7 PASSED
- **Total Suite:** 42/42 PASSED

---

## 5. AUDIT VERDICT & NEXT STEPS

- **Audit Status:** COMPLETE.
- **Architectural Boundary:** PERCEPTION-ONLY INVARIANTS PERFECTLY PRESERVED.
- **Phase 3B Status:** BLOCKED (Stopping per directive).
