# Sentinel Crown Demo — Final Integrated Demonstration Review

## Core Thesis & Principle
> **"THE MODEL SEES. SENTINEL INVESTIGATES."**

---

## 1. Demo Flow
The Crown Demo provides a unified, continuous investigation journey across 10 sequential screens/sections:
1. **Screen 1 — Project Discovery**: Ward 7 Stormwater Drainage Improvement Overview (₹18L Sanctioned, ₹7.2L Released, 80% Claimed).
2. **Screen 2 — Investigation Execution**: Real-time state machine progression with checkmarks.
3. **Screen 3 — Evidence Graph**: Visual graph connecting claims to physical, financial, and vision nodes.
4. **Screen 4 — Sentinel Finding**: Citizen-safe plain language findings (`HUMAN REVIEW REQUIRED`).
5. **Screen 5 — Human Review & Auditor Correction**: Auditor review action preserving original interpretation while storing correction.
6. **Screen 6 — Sentinel Learned**: Visually prominent institutional memory card explaining the precedent rule.
7. **Screen 7 — Ward 8 Case Transition**: Transitioning to second case (Ward 8, 500m certified vs 220m visible).
8. **Screen 8 — Historical Precedent Surfaced**: Displaying retrieved precedent tagged explicitly with `PRECEDENT ≠ PROOF`.
9. **Screen 9 — Current Evidence Recheck**: Re-checking Ward 8 current evidence independently without auto-closure.
10. **Screen 10 — Final Summary & Core Principle**: Closing minimal screen emphasizing structured case memory context.

---

## 2. Backend Operations Used
- **Database (`SentinelDB`)**: SQLite in-memory / persistent database as single source of truth.
- **Service Layer (`SentinelCitizenAPI`)**: Exposes REST endpoints serving public project overview, money trail, evidence graph, investigation status, human corrections, and precedent retrieval.
- **Orchestrator (`SentinelOrchestrator`)**: Executes the 12-stage state machine (`DISCOVER` through `CURRENT_EVIDENCE_RECHECKED`).
- **Vision Adapter (`ConstructionPerceptionAdapter`)**: Ingests site photos and emits perception nodes (`NEUTRAL` relationship).
- **Contradiction Engine (`ContradictionEngine`)**: Identifies physical measurement gaps (e.g. 400m vs 180m).
- **Decision Engine (`DecisionEngine`)**: Evaluates evidence strength and emits authoritative verdicts (`HUMAN_REVIEW_REQUIRED`).
- **Case Memory Engine (`CaseMemoryEngine`)**: Persists structured `CaseMemoryRecord` items for pattern retrieval.

---

## 3. UI Screens
- Clean responsive dark-mode interface built with HTML5/JS/Vanilla CSS.
- Features top state machine timeline bar, step-by-step guided story navigation, interactive node badges, color-coded evidence relationships (`SUPPORTS` green, `CONTRADICTS` red, `NEUTRAL` blue, `INSUFFICIENT` amber), and auditor correction form.

---

## 4. Evidence Shown
- **Ward 7**:
  - `MB-402`: 400.0m certified work (SUPPORTS claim)
  - `INSP-009`: 180.0m visible inside open trench (CONTRADICTS claim)
  - `CONST-VISION`: Construction machinery, PPE, site personnel observed (NEUTRAL context)
  - `TREASURY-01`: ₹7,20,000 released tranche (INSUFFICIENT / NEUTRAL)
- **Ward 8**:
  - `MB-505`: 500.0m certified work (SUPPORTS claim)
  - `INSP-012`: 220.0m visible inside open trench (CONTRADICTS claim)

---

## 5. Human Correction Flow
- Auditor submits:
  - Corrected interpretation: *"The missing section was underground/backfilled and therefore was not visible during inspection."*
  - Reason: *"Underground/backfilled infrastructure may not remain visually observable after completion."*
- **Non-Overwrite Invariant**: Original interpretation is preserved immutably alongside human correction in `human_corrections` table.

---

## 6. Case Memory Flow
- Generates `CaseMemoryRecord` containing:
  - Pattern type: `STAGED_MATERIAL_DISCREPANCY` / `UNDERGROUND_INFRASTRUCTURE`
  - Precedent rule: *"Certified infrastructure may exceed visible surface evidence when work is underground or backfilled."*
- Explicitly clarified in UI/API: **This is structured case memory retrieval, NOT model-weight retraining.**

---

## 7. Historical Precedent Flow
- Ward 8 investigation automatically queries case memory store.
- Surfaces retrieved pattern with prominent badge: **`HISTORICAL PRECEDENT`**.
- Displays callout tag: **`PRECEDENT ≠ PROOF`** (*"The previous case informs investigation context but does not determine this case."*).

---

## 8. Ward 8 Independent Evaluation
- Ward 8's current evidence (500m MB vs 220m photo) is evaluated on its own merits by the Decision Engine.
- Ward 7 correction provides context but **does NOT auto-close or auto-resolve** Ward 8.

---

## 9. Safety & Semantic Boundaries
- Zero legal accusations or fraud terminology (`FRAUD`, `GUILT`, `PAYMENT_DENIAL`, `CLAIM_IS_FALSE`).
- Vision sensor nodes emit strictly `NEUTRAL` relationships and never make final financial decisions.
- Public API responses conceal internal prompts, auditor IDs, and secret API keys.

---

## 10. Test Results
- **Full Test Suite Status**: **129 / 129 tests passed 100%** (`python -m unittest discover -s tests -p "test_*.py"`).
- Test execution time: 6.77s.

---

## 11. Known Limitations
- Demo imagery uses representative civil engineering site samples; full deployment will integrate live RTSP drone feed adapters.
- Case memory pattern matching relies on structured key/tag matching; semantic vector indexing can be added in future without modifying data schemas.

---

## 12. Exact Demo Startup Instructions

### 1. Run Command-Line Audit Trail Demo:
```powershell
.\.venv\Scripts\python.exe scripts/run_crown_demo.py
```

### 2. Start Web Server & Open Citizen Portal:
```powershell
.\.venv\Scripts\python.exe scripts/start_server.py
```
Open web browser at: [http://localhost:8000](http://localhost:8000)

### 3. Run Test Suite Verification:
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```
