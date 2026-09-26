# SENTINEL Phase 2B.1 Architectural Review

> **System:** SENTINEL — Agentic Evidence Intelligence System  
> **Phase:** 2B.1 (Vision Boundary Correction — Perception-Only Perception Architecture)  
> **Status:** Architecture Correction Implemented & All 35 Automated Tests Passing  

---

## 1. Architectural Rationale & Pipeline Correction

In Phase 2B.1, an architectural correction was applied to enforce the principle that **the Vision Adapter MUST be Perception-Only**.

Previously, the Vision Adapter assigned analytical relationship labels (`CONTRADICTS` or `SUPPORTS`) during initial image normalization based on simple value comparisons. This violated the core Sentinel architectural boundary: perception models must only report *what is observed*, leaving analytical relationship judgments (`CONTRADICTS`, `SUPPORTS`, `INSUFFICIENT`) to downstream orchestration and contradiction evaluation layers.

### Corrected Perception-to-Decision Pipeline:

```
                          Raw Site Photograph / Drone Image
                                        │
                                        ▼
                            Mock Vision Simulator
                    (mock-yolov8-drainage-v1 Pipe Detection)
                                        │
                                        ▼
                            Vision Evidence Adapter
                       (PERCEPTION-ONLY: relationship = 'NEUTRAL')
                                        │
                       Normalizes observation, confidence,
                       location & bounding box telemetry
                                        │
                                        ▼
                        Supabase PostgreSQL / SentinelDB
                             (evidence.metadata JSONB)
                                        │
                                        ▼
                           Contradiction Engine
                    (Analyzes Physical Discrepancy & Sets
                     HIGH Severity Contradiction Edge)
                                        │
                                        ├──────────────────────────┐
                                        ▼                          ▼
                             Orchestrator Decision        Citizen Evidence Graph
                          (HUMAN_REVIEW_REQUIRED State)    (Renders Contradiction Badge ✕)
```

---

## 2. Code Changes Summary

1. [`src/sentinel/vision/adapter.py`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/src/sentinel/vision/adapter.py)
   - Removed analytical comparison logic (`SUPPORTS`/`CONTRADICTS`) from the Vision Adapter.
   - All raw vision observations enter the Evidence Contract as `relationship = "NEUTRAL"` (or `"INSUFFICIENT"` if low confidence).
   - Preserves all bounding box vectors, camera EXIF headers, and vision model IDs.

2. [`src/sentinel/engines/contradiction_engine.py`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/src/sentinel/engines/contradiction_engine.py)
   - Added analytical relationship evaluation comparing physical measurement evidence pairs (e.g. MB certified 400m vs Physical photo inspection / Geo photo 180m).
   - Flags high-severity quantitative physical contradictions directly from raw observations.

3. [`src/sentinel/api.py`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/src/sentinel/api.py)
   - Updated `get_evidence_graph` to cross-reference active `contradictions` records in the database.
   - Renders contradiction badges (`CONTRADICTS` / `✕`) on evidence nodes when flagged by the Contradiction Engine.

4. [`tests/test_sentinel_phase2b.py`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/tests/test_sentinel_phase2b.py)
   - Updated unit tests proving:
     1. Vision Adapter never independently labels an observation `CONTRADICTS` (defaults to `NEUTRAL` on intake).
     2. Contradiction Engine identifies 180m vs 400m conflict.
     3. Investigation reaches `HUMAN_REVIEW_REQUIRED`.
     4. Evidence Graph API renders the resulting contradiction node with `✕` badge.
     5. All 35 tests pass cleanly.

---

## 3. Automated Test Execution & Results

Command: `python -m unittest discover -s tests -p "test_*.py" -v`

### Complete Test Suite Status (35 / 35 PASSED):

| Test Suite | Test Case | Purpose / Feature Tested | Status |
| :--- | :--- | :--- | :--- |
| **Phase 1A** | `test_1` - `test_10` | Deterministic Investigation, Contradictions, RLS, FK Integrity | **10/10 PASS** |
| **Phase 1B** | `test_1` - `test_10` | Claude Integration, Schema Validation, Grounding, Fallbacks | **10/10 PASS** |
| **Phase 2A** | `test_1` - `test_8` | Citizen API, Money Trail, Evidence Graph UI, Security Isolation | **8/8 PASS** |
| **Phase 2B.1** | `test_1_vision_simulator_output` | Simulator generates bounding box telemetry and measurements | **PASS** |
| **Phase 2B.1** | `test_2_vision_adapter_perception_only_neutral` | Adapter sets relationship to `NEUTRAL` (Perception-Only boundary) | **PASS** |
| **Phase 2B.1** | `test_3_metadata_preservation` | `bounding_boxes`, `exif`, and `vision_model` preserved in JSONB | **PASS** |
| **Phase 2B.1** | `test_4_vision_db_ingestion` | Vision evidence persists in DB as `NEUTRAL` observation | **PASS** |
| **Phase 2B.1** | `test_5_contradiction_engine_identifies_conflict` | Contradiction Engine evaluates 180m vs 400m and flags conflict | **PASS** |
| **Phase 2B.1** | `test_6_vision_orchestration_reaches_human_review` | Orchestrator reaches `HUMAN_REVIEW_REQUIRED` | **PASS** |
| **Phase 2B.1** | `test_7_vision_node_render_in_citizen_graph_api` | Citizen Graph API renders contradiction badge `✕` for Engine edge | **PASS** |

**Total Suite Result:** `35 / 35 PASSED`

---

## 4. Phase 2B.1 System Verdict

The perception-only vision boundary correction is complete, fully tested, and documented.
All 35 automated tests are passing.
