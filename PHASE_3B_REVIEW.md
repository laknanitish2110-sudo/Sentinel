# SENTINEL PHASE 3B — CONSTRUCTION PERCEPTION LAYER REVIEW

**Status:** APPROVED & VERIFIED  
**Date:** September 26, 2026  
**Test Suite:** 55/55 PASSED  

---

## 1. EXECUTIVE SUMMARY

Phase 3B introduces the **Construction Perception Layer** (`ConstructionEventInterpreter` & `taxonomy.py`) into SENTINEL's vision pipeline. It maps raw object detections into a structured construction taxonomy without falsely claiming that generic COCO models (like pretrained YOLOv8n) detect construction-specific assets that they were not trained on.

---

## 2. ARCHITECTURAL TAXONOMY & UNCERTAINTY MODEL

```
+--------------------------+      +---------------------------+      +-----------------------------+
| Raw Model Class          | ---> | Visual Primitive          | ---> | Perception Event            |
| (e.g., "truck", "person")|      | ("construction_equipment")|      | ("possible_material_delivery")|
+--------------------------+      +---------------------------+      +-----------------------------+
                                                                                  |
                                                                                  v
+--------------------------+      +---------------------------+      +-----------------------------+
| Evidence Contract        | <--- | Full Model Provenance     | <--- | Explicit Uncertainty        |
| (relationship = NEUTRAL) |      | (bounding_box, confidence)|      | (uncertainty = 1 - conf)    |
+--------------------------+      +---------------------------+      +-----------------------------+
```

### Visual Primitives vs. Perception Events

1. **Visual Primitives (`VisualPrimitive`)**:
   - Observational object categories anchored directly to physical objects (e.g., `pipe`, `trench`, `worker`, `construction_equipment`, `road_surface`).
2. **Perception Events (`PerceptionEvent`)**:
   - Higher-level site activity hypotheses.
   - Every event explicitly carries the `possible_` prefix (e.g., `possible_pipe_installation`, `possible_excavation_activity`, `possible_material_delivery`, `possible_construction_activity`).

---

## 3. KEY ARCHITECTURAL INVARIANTS

### 1. Honest Model Representation (No Class Fabrication)
- Pretrained `yolov8n.pt` operates on COCO object classes.
- Generic unmapped classes (e.g. `kite`, `dog`, `bottle`) **do NOT** produce fabricated construction primitives or events; they are left unmapped.
- Only legitimate, defensible mappings (e.g., COCO `truck` -> `construction_equipment`, `person` -> `worker`) trigger construction perception event hypotheses.

### 2. Explicit Uncertainty Preservation
- Model confidence is preserved (`model_confidence = 0.88`).
- Uncertainty is explicitly computed and stored (`uncertainty_score = 1 - confidence = 0.12`).
- The system never claims 100% certainty or certified measurement authority over observational vision estimates.

### 3. Complete Provenance Preservation
Every event record maintains full trace provenance back to the raw vision detection:
- `source_evidence_id`
- `original_model_class`
- `model_confidence`
- `bounding_box`
- `image_dimensions`
- `model_checkpoint_identifier` (`yolov8n.pt`)
- `timestamp` & `location`
- `interpreter_version` (`v3B-perception-interpreter-1.0`)
- `taxonomy_version` (`v3B-perception-taxonomy-1.0`)

### 4. Perception-Only Boundary & Safety Filters
- All interpreted perception events carry `relationship = "NEUTRAL"`.
- The interpreter strictly rejects forbidden financial, legal, or fraud judgment terms (`COMPLETED_PROJECT`, `FRAUDULENT`, `FRAUD`, `INVALID_CLAIM`, `PAYMENT_DENIAL`, `VERIFIED_COMPLETION`).

---

## 4. SAMPLE INTERPRETED PERCEPTION EVENT PAYLOAD

```json
{
  "event_id": "evt_a1b2c3d4",
  "source_evidence_id": "evi_test_phase3b_001",
  "perception_event": "possible_material_delivery",
  "visual_primitive": "construction_equipment",
  "original_model_class": "truck",
  "model_confidence": 0.88,
  "uncertainty_score": 0.12,
  "bounding_box": [100, 200, 500, 800],
  "image_dimensions": "1920x1080",
  "model_checkpoint_identifier": "yolov8n.pt",
  "timestamp": "2026-09-20T10:00:00Z",
  "location": {
    "latitude": 12.972,
    "longitude": 77.595
  },
  "interpreter_version": "v3B-perception-interpreter-1.0",
  "taxonomy_version": "v3B-perception-taxonomy-1.0",
  "relationship": "NEUTRAL",
  "observation_description": "Perception interpreter (v3B-perception-interpreter-1.0) identified possible_material_delivery from visual primitive 'construction_equipment' (raw model class 'truck', conf: 0.88)."
}
```

---

## 5. TEST SUITE VERIFICATION RESULT

```
python -m unittest discover -s tests -p "test_*.py" -v
----------------------------------------------------------------------
Ran 55 tests in 3.004s

OK
```

- **Phase 1A Tests:** 10/10 PASSED
- **Phase 1B Tests:** 10/10 PASSED
- **Phase 2A Tests:** 8/8 PASSED
- **Phase 2B.1 Tests:** 7/7 PASSED
- **Phase 3A Tests:** 7/7 PASSED
- **Phase 3A.1 Tests:** 5/5 PASSED
- **Phase 3B Tests:** 8/8 PASSED
- **Total Suite:** 55/55 PASSED

---

## 6. PHASE 3B BOUNDARIES & STOPPING CONDITION

- **No Custom Fine-Tuning Executed.**
- **No Live Video / Camera Tracking Implemented.**
- **No Decision Engine / Contradiction Semantics Changed.**
- **Phase 3B Complete. Stopping per instruction.**
