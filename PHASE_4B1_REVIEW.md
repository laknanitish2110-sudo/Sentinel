# SENTINEL PHASE 4B.1 — GENUINE CONSTRUCTION EVIDENCE VALIDATION REVIEW

**Status:** PASS & VERIFIED (Correction Pass Applied)  
**Date:** September 26, 2026  
**Evaluated Images:** 3 Genuine Construction Site Photographs  
**Model Checkpoint:** Pretrained `yolov8n.pt` (Ultralytics COCO 80-class)  

---

## 1. DATASET PROVENANCE & LICENSING

The evaluation dataset stored in [`data/vision_eval_real/`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/data/vision_eval_real/) consists strictly of un-manipulated real-world construction site photographs with verified, authentic licensing from Wikimedia Commons:

| Image Filename | Source & Canonical URL | Author / Artist | Exact License | Attribution Required | EXIF / GPS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`real_eval_01_concrete_pump_truck.jpg`** | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Construction_site_with_concrete_pump_truck.JPG) | Steve Pivnick, U.S. Air Force | Public Domain | None | EXIF: Yes, GPS: No |
| **`real_eval_02_construction_works_osaka.jpg`** | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Construction_works_Japan,_Osaka.jpg) | Editorq35 | CC BY-SA 4.0 | Attribute to Editorq35 | EXIF: Yes, GPS: No |
| **`real_eval_03_construction_labour_workers.jpg`** | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:House_Construction_Labour_Workers_1_-_Invermere,_British_Columbia.jpg) | PatInver | CC BY-SA 4.0 | Attribute to PatInver | EXIF: Yes, GPS: No |

*Full metadata and direct canonical source links are documented in [`data/vision_eval_real/README.md`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/data/vision_eval_real/README.md).*

---

## 2. ACTUAL MODEL CONFIGURATION

- **Architecture**: Ultralytics YOLOv8 Nano (`YOLOv8n`)
- **Weights Identifier**: `yolov8n.pt`
- **Training Taxonomy**: COCO 80-class standard object detection taxonomy
- **Inference Parameter**: `conf = 0.25`
- **Perception Pipeline Integration**: Detections ingested via `YOLODetector` -> `ConstructionEventInterpreter` -> `EvidenceGraph`
- **Perception Bounds**: Perception-only. Output relationship strictly `NEUTRAL`. Zero unsupported class fabrication.

---

## 3. ACTUAL DETECTIONS PER IMAGE

Below are the empirical tensor inference detections produced by `yolov8n.pt` on the real evidence set under conservative perception semantics:

### Image 1: `real_eval_01_concrete_pump_truck.jpg`
- **Raw Bounding Boxes (5 detected)**:
  - `car` (conf: 0.4493, bbox: `[562, 216, 599, 309]`)
  - `person` (conf: 0.4315, bbox: `[439, 1465, 558, 1543]`)
  - `person` (conf: 0.3049, bbox: `[950, 1617, 1073, 1670]`)
  - `car` (conf: 0.2984, bbox: `[544, 409, 573, 476]`)
  - `umbrella` (conf: 0.2782, bbox: `[566, 78, 634, 163]`)
- **Interpreted Perception Events (2 events)**:
  - `possible_construction_activity` | Primitive: `worker` | COCO class: `person` | Conf: 0.4315 | Relationship: `NEUTRAL`
  - `possible_construction_activity` | Primitive: `worker` | COCO class: `person` | Conf: 0.3049 | Relationship: `NEUTRAL`

### Image 2: `real_eval_02_construction_works_osaka.jpg`
- **Raw Bounding Boxes (3 detected)**:
  - `truck` (conf: 0.8728, bbox: `[752, 1763, 2077, 4024]`)
  - `person` (conf: 0.8635, bbox: `[1246, 906, 2151, 1270]`)
  - `person` (conf: 0.8430, bbox: `[1168, 337, 1990, 623]`)
- **Interpreted Perception Events (3 events)**:
  - `possible_construction_activity` | Primitive: `construction_equipment` | COCO class: `truck` | Conf: 0.8728 | Relationship: `NEUTRAL`
  - `possible_construction_activity` | Primitive: `worker` | COCO class: `person` | Conf: 0.8635 | Relationship: `NEUTRAL`
  - `possible_construction_activity` | Primitive: `worker` | COCO class: `person` | Conf: 0.8430 | Relationship: `NEUTRAL`

### Image 3: `real_eval_03_construction_labour_workers.jpg`
- **Raw Bounding Boxes (6 detected)**:
  - `truck` (conf: 0.7963, bbox: `[232, 988, 467, 1613]`)
  - `person` (conf: 0.7959, bbox: `[516, 950, 749, 1052]`)
  - `person` (conf: 0.7798, bbox: `[442, 300, 589, 390]`)
  - `person` (conf: 0.4902, bbox: `[383, 662, 635, 812]`)
  - `person` (conf: 0.4661, bbox: `[432, 376, 703, 510]`)
  - `car` (conf: 0.2662, bbox: `[266, 933, 331, 1012]`)
- **Interpreted Perception Events (5 events)**:
  - `possible_construction_activity` | Primitive: `construction_equipment` | COCO class: `truck` | Conf: 0.7963 | Relationship: `NEUTRAL`
  - `possible_construction_activity` | Primitive: `worker` | COCO class: `person` | Conf: 0.7959 | Relationship: `NEUTRAL`
  - `possible_construction_activity` | Primitive: `worker` | COCO class: `person` | Conf: 0.7798 | Relationship: `NEUTRAL`
  - `possible_construction_activity` | Primitive: `worker` | COCO class: `person` | Conf: 0.4902 | Relationship: `NEUTRAL`
  - `possible_construction_activity` | Primitive: `worker` | COCO class: `person` | Conf: 0.4661 | Relationship: `NEUTRAL`

---

## 4. CONSTRUCTION PRIMITIVE COVERAGE TABLE

| Construction Primitive | Model Support | Actual Evidence (COCO Class) | Actual Confidence Range | Limitations |
| :--- | :--- | :--- | :--- | :--- |
| **`worker`** | **`PARTIALLY_SUPPORTED`** | `person` | $0.3049 - 0.8635$ | COCO `person` proves human presence; does NOT prove worker identity or trade qualification. |
| **`construction_equipment`** | **`PARTIALLY_SUPPORTED`** | `truck` | $0.7963 - 0.8728$ | COCO `truck` proves heavy vehicle presence; does NOT prove material delivery by itself. |
| **`pipe`** | **`NOT_SUPPORTED`** | None | N/A | COCO 80 classes do not include utility/drainage pipe classes. |
| **`trench`** | **`NOT_SUPPORTED`** | None | N/A | Ground earthworks and excavated trenches are unrepresented in COCO taxonomy. |
| **`manhole`** | **`NOT_SUPPORTED`** | None | N/A | Utility inspection chambers/manholes are unrepresented in COCO taxonomy. |
| **`excavator`** | **`NOT_SUPPORTED`** | None | N/A | COCO lacks heavy machinery breakdown (`excavator`, `backhoe`, `grader`). |
| **`concrete`** | **`NOT_SUPPORTED`** | None | N/A | Surface material classification is unavailable in bounding-box detector. |
| **`gravel`** | **`NOT_SUPPORTED`** | None | N/A | Bulk aggregate material classification is unavailable in standard YOLO detector. |
| **`soil`** | **`NOT_SUPPORTED`** | None | N/A | Earthwork soil classification is unavailable in standard YOLO detector. |
| **`material_stack`** | **`NOT_SUPPORTED`** | None | N/A | Staged building supply stacks are not segmented by COCO 80 classes. |
| **`road_surface`** | **`NOT_SUPPORTED`** | None | N/A | Pavement and road surface layer segmentation is absent. |

---

## 5. WHAT YOLOV8N COCO CAN GENUINELY OBSERVE

1. **Human Site Presence**: COCO `person` detections identify human presence on site (conf: 0.30 - 0.86).
2. **Heavy Vehicle Presence**: COCO `truck` detections identify heavy vehicle presence (conf: 0.79 - 0.87).
3. **Generic Vehicle Presence**: COCO `car` detections identify site transport vehicles.

---

## 6. WHAT IT CANNOT OBSERVE

1. **Civil Engineering Infrastructure**: Cannot detect laid or staged pipes (`pipe`), earth trenches (`trench`), or manhole structures (`manhole`).
2. **Heavy Machinery Categorization**: Cannot distinguish excavators, bulldozers, or concrete pumps from generic trucks or un-mapped objects.
3. **Material Composition & Delivery Events**: Cannot infer material delivery business events from vehicle presence alone.
4. **Physical Dimensions**: Cannot measure linear length or volumetric quantities without 3D photogrammetry/depth sensors.

---

## 7. CAPABILITIES REQUIRING A SPECIALIZED CONSTRUCTION MODEL

1. **Domain-Specific Fine-Tuned Object Detector**: Custom YOLO model trained on annotated civil engineering datasets (trench excavations, PVC/RCC pipes, manhole covers, excavators).
2. **Material Segmentation Model**: Semantic segmentation network for soil, gravel, concrete, and asphalt classification.
3. **Photogrammetric / Stereo Depth Estimator**: Spatial point cloud or monocular depth model to estimate physical trench depth and pipe lengths in metric units.

---

## 8. SUFFICIENCY FOR SENTINEL DEMO

- **Architecture & System Pipeline: 100% SUFFICIENT.**
  The Sentinel system cleanly handles real-world vision inputs, enforces strict perception-only `NEUTRAL` relationship bounds, preserves full EXIF and source evidence provenance, and feeds non-accusatory events into the Spatial-Temporal Engine and Case Memory.
- **Perception Domain Baseline:**
  Generic COCO detections establish a conservative baseline of site activity (`worker` and `construction_equipment` presence) without fabricating false civil engineering or business delivery facts.

---

## 9. EXPLICIT LIMITATIONS

1. **No Automated Civil Claim Verification from Pretrained COCO Alone**: Claim verification requires multi-source evidence (official contracts, spatial-temporal context, engineer logs) combined with specialized vision models.
2. **Proxy Class Reliance**: Using `person` as a proxy for `worker` and `truck` as a proxy for `construction_equipment` provides generic site presence evidence but lacks specialized trade verification.
3. **Absence of Ground Metadata**: Camera EXIF headers on tested web samples lacked embedded GPS tags (latitude/longitude), requiring location overrides or external telemetry when building spatial evidence graphs.

---

## 10. SEMANTIC SAFETY CORRECTIONS

- **Vision Detects Visual Primitives, Not Business Events**:
  Visual object detectors emit bounding boxes and basic class labels (e.g. `truck`, `person`). Vision perception layers must NOT automatically convert raw visual primitives into commercial or contract business conclusions (such as `material_delivered`, `delivery_verified`, or `payment_approval`).
- **Material Delivery Requires Downstream Corroboration**:
  A vehicle/truck detection provides evidence of heavy vehicle presence (`possible_construction_activity`). Establishing an actual material delivery event requires downstream multi-evidence corroboration (e.g., delivery tickets, weighbridge logs, supervisor timestamps, and location matching).
- **Person Detection Does Not Prove Worker Identity**:
  Detecting COCO `person` proves human site presence. It does not verify trade qualification, contractor identity, high-visibility vest compliance, or employment status.
- **Construction-Specific Conclusions Require Multi-Source Evidence**:
  Sentinel enforces strict perception-only boundaries: vision output is ingested as neutral observation telemetry. Conclusive findings are formulated exclusively by the downstream Orchestrator and Decision Engine when corroborated by cross-source evidence.
