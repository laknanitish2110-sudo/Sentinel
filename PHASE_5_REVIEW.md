# Sentinel Phase 5 — Investigation Loop Integration Review

## Executive Summary
Phase 5 successfully integrates Sentinel's core components into one complete end-to-end investigation workflow. The pipeline seamlessly executes from Citizen Investigation trigger to multi-source evidence collection, graph construction, quantitative contradiction detection, Decision Engine evaluation (`HUMAN_REVIEW_REQUIRED`), plain-language citizen explanation generation, auditor review/correction, structured case memory recording, and subsequent multi-investigation historical precedent retrieval (Ward 8 demo case).

---

## 1. Existing Architecture Reused
No new orchestrators, databases, agent frameworks, microservices, vector search engines, or vision models were added. The system relies strictly on the locked architecture:
```
CITIZEN (UI/API)
  ↓
INVESTIGATION GOAL
  ↓
ORCHESTRATOR (SentinelOrchestrator)
  ↓
EVIDENCE SOURCES (Financial, MB Inspection, Case Memory, Vision Perception)
  ↓
EVIDENCE CONTRACT (EvidenceItem, Provenance, Uncertainty)
  ↓
EVIDENCE GRAPH (SentinelDB / Graph representation)
  ↓
CONTRADICTION ENGINE (Quantitative & Temporal Discrepancies)
  ↓
DECISION ENGINE (Sole authority: SUPPORTED, PARTIALLY_SUPPORTED, INSUFFICIENT_EVIDENCE, HUMAN_REVIEW_REQUIRED)
  ↓
HUMAN REVIEW & HUMAN CORRECTION (Auditor UI/API)
  ↓
CASE MEMORY (CaseMemoryRecord / Pattern Storage)
  ↓
FUTURE INVESTIGATION (Historical Precedent Retrieval)
```

---

## 2. Investigation Lifecycle
The investigation lifecycle follows an explicit 12-stage state machine (`InvestigationState` enum):
1. **DISCOVER**: Project selected by citizen/auditor (`DEMO-WARD7-DRAIN-2026`).
2. **INVESTIGATE**: `trigger_investigation()` invoked via API/UI.
3. **ANALYZING_EVIDENCE**: Multi-source evidence gathered asynchronously via registered adapters/agents.
4. **EVIDENCE_GRAPH**: Unified evidence nodes & relationships compiled.
5. **CONFLICT_DETECTED**: Physical measurement discrepancy identified by Contradiction Engine (400m certified vs 180m visible).
6. **HUMAN_REVIEW_REQUIRED**: Decision Engine produces final evaluation.
7. **CITIZEN_EXPLANATION_GENERATED**: Citizen-safe plain language summary compiled.
8. **HUMAN_CORRECTION**: Auditor submits contextual explanation ("Underground/backfilled section not visible during initial surface survey").
9. **LEARNING_STORED**: Case memory record created with pattern hash & precedent rule.
10. **SIMILAR_CASE**: Second project (`DEMO-WARD8-DRAIN-2026`) investigation initiated.
11. **PRECEDENT_SURFACED**: Relevant case memory retrieved as `HISTORICAL_PRECEDENT`.
12. **CURRENT_EVIDENCE_RECHECKED**: Current evidence evaluated independently; precedent provides context without auto-closing or auto-resolving.

---

## 3. Evidence Sources
The Ward 7 demonstration uses 4 genuine evidence sources adhering strictly to the Sentinel Evidence Contract:
1. **Financial & Project Records**: ₹18,00,000 sanctioned, ₹7,20,000 released, 80% completion claimed.
2. **Official Measurement Records**: MB-402 entry certifying 400 meters completed.
3. **Inspection Evidence**: Visual/physical survey report recording 180 meters visible.
4. **Vision / Construction Perception**: YOLO visual observations (construction machinery, PPE, site personnel present).

Every record retains complete hash/source provenance (`source_url`, `author`, `confidence`, `timestamp`).

---

## 4. Evidence Graph Behavior
The Evidence Graph links the project claim node (`CLAIM-WARD7-COMPLETION`) to evidence nodes:
- `MB-402` node (400m certified) → **SUPPORTS** claim.
- `Inspection Photo` node (180m visible) → **CONTRADICTS** MB-402 certified length.
- `Vision Perception` node (machinery present) → **NEUTRAL** / **CONTEXTUAL** (visual activity presence does not independently prove length).
- Graph semantics are governed strictly by the reasoning layer; visual sensors emit `NEUTRAL` relationships by default.

---

## 5. Contradiction Behavior
The Contradiction Engine analyzes physical discrepancies:
- Compares certified physical metric (400m) against verified visual observation (180m).
- Detects a quantitative gap of **220 meters** (55% variance).
- Categorizes discrepancy as `QUANTITATIVE_DISCREPANCY` with `HIGH` severity.
- Vision observations of machinery/personnel are kept neutral and do not independently create financial contradictions.

---

## 6. Decision Behavior
The Decision Engine retains sole authority over investigation verdicts:
- Evaluates evidence strength, source reliability, and contradiction severity.
- Renders **HUMAN_REVIEW_REQUIRED** for Ward 7 due to unresolved physical discrepancy.
- Strictly enforces safety boundaries:
  - **No automated fraud verdicts** or accusatory language.
  - **No automated payment denial** or sanction cancellation.
  - **No individual AI model/agent override** of the Decision Engine.

---

## 7. Human Correction Behavior
Auditors can submit structured corrections via `submit_human_correction()`:
- Accepts `corrected_interpretation`, `reason`, `linked_evidence_ids`, and `auditor_id`.
- **Preservation Invariant**: Original interpretation is preserved immutably alongside the human correction.
- Persisted in `human_corrections` table with timestamp and investigation reference.

---

## 8. Case Memory Behavior
Upon human correction submission, a `CaseMemoryRecord` is instantiated:
- Extracts structural pattern ("certified length exceeding visible surface inspection in backfilled drainage works").
- Stores precedent rule ("Underground backfilling may obscure completed length during surface visual inspection").
- Links original evidence IDs and human correction record ID.
- No model weight retraining is claimed; this functions strictly as structured, reproducible case retrieval.

---

## 9. Historical Precedent Behavior
When investigating subsequent projects with similar evidence patterns (e.g., Ward 8):
- Retrieves relevant case memories by matching project types and discrepancy tags.
- Surfaces retrieved items clearly tagged as **HISTORICAL PRECEDENT**.
- Emits explicit rationale noting prior auditor finding regarding backfilled infrastructure.

---

## 10. Second-Case Behavior (Ward 8)
- Ward 8 (`DEMO-WARD8-DRAIN-2026`) features 500m claimed vs 220m visible.
- Historical precedent from Ward 7 is attached as context.
- **Independence Invariant**: Ward 8 current evidence is evaluated independently.
- **No Auto-Resolution**: Precedent does NOT auto-close or auto-resolve Ward 8. The Decision Engine re-checks current evidence independently.

---

## 11. Citizen-Safe Explanation
The citizen-facing UI and API expose plain-language summaries (`get_citizen_explanation()`):
- Structure:
  - **WHAT SENTINEL FOUND**: Factual findings from official records and visual inspections.
  - **WHY THIS MATTERS**: Plain-language explanation of why reconciliation is required.
  - **CURRENT STATUS**: Clear display of `HUMAN REVIEW REQUIRED`.
- **Security & Privacy Boundary**: Internal prompts, auditor IDs, chain-of-thought, database keys, and backend API keys are strictly excluded.

---

## 12. Test Results
The full test suite containing **123 tests** passed cleanly (0 failures, 0 errors):
- 108 existing tests (Phase 1 through Phase 4C) preserved and passing.
- 15 new Phase 5 integration tests covering end-to-end investigation, contradiction detection, decision engine verdicts, human correction, case memory, precedent retrieval, citizen safety, and API endpoints.

---

## 13. Any Architectural Changes
**Zero architectural changes.** The system reuses existing SQLite schema (`sentinel.db`), existing data models (`EvidenceItem`, `CaseMemoryRecord`, `InvestigationState`), existing engines (`ContradictionEngine`, `DecisionEngine`), and existing UI routes.

---

## 14. Any Limitations
- Precedent matching uses pattern key matching; full semantic embedding vector search can be integrated in future phases without altering data contracts.
- Camera calibration/3D point-cloud estimation is not included; length validation relies on calibrated target physical tags or manual inspection corroboration.
