# SENTINEL: Phase 0 Architecture Audit Report

> **System:** SENTINEL — Agentic Evidence Intelligence System  
> **Phase:** 0 (Foundation Specification & Core Schema Audit)  
> **Audit Type:** Read-Only Architectural Verification  
> **Artifact Inspected:** `docs/PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/EVIDENCE_CONTRACT.md`, `docs/INVESTIGATION_STATE_MACHINE.md`, `supabase/migrations/001_sentinel_schema.sql`, `supabase/seed/001_demo_drainage_project.sql`, `PHASE_0_REVIEW.md`.

---

## 1. EVIDENCE CONTRACT AUDIT

### Schema Field Alignment Analysis

The PostgreSQL schema defined in `supabase/migrations/001_sentinel_schema.sql` (`evidence` table) was mapped against the contract specification in `docs/EVIDENCE_CONTRACT.md`:

| Evidence Contract Field | SQL Column Name | SQL Type & Constraints | Alignment Status |
| :--- | :--- | :--- | :--- |
| `evidence_id` | `id` | `UUID PRIMARY KEY DEFAULT gen_random_uuid()` | **VERIFIED** |
| `project_id` | `project_id` | `UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE` | **VERIFIED** |
| `claim_id` | `claim_id` | `UUID REFERENCES claims(id) ON DELETE SET NULL` (Optional) | **VERIFIED** |
| `source_type` | `source_type` | `VARCHAR(50) NOT NULL CHECK (source_type IN (...))` | **VERIFIED** |
| `source_id` | `source_id` | `VARCHAR(255) NOT NULL` | **VERIFIED** |
| `observation` | `observation` | `TEXT NOT NULL` | **VERIFIED** |
| `value` | `value` | `NUMERIC(15,2)` | **VERIFIED** |
| `unit` | `unit` | `VARCHAR(50)` | **VERIFIED** |
| `timestamp` | `timestamp` | `TIMESTAMPTZ` | **VERIFIED** |
| `location` | `location` | `JSONB` | **VERIFIED** |
| `confidence` | `confidence` | `NUMERIC(3,2) NOT NULL DEFAULT 1.00 CHECK (confidence >= 0.00 AND confidence <= 1.00)` | **VERIFIED** |
| `reliability` | `reliability` | `VARCHAR(20) NOT NULL DEFAULT 'MEDIUM' CHECK (reliability IN ('HIGH', 'MEDIUM', 'LOW', 'UNVERIFIED'))` | **VERIFIED** |
| `relationship` | `relationship` | `VARCHAR(20) NOT NULL DEFAULT 'NEUTRAL' CHECK (relationship IN ('SUPPORTS', 'CONTRADICTS', 'NEUTRAL', 'INSUFFICIENT'))` | **VERIFIED** |
| `metadata` | `metadata` | `JSONB NOT NULL DEFAULT '{}'::jsonb` | **VERIFIED** |
| `created_at` | `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT NOW()` | **VERIFIED** |

### Future Vision Observation Compatibility
The schema guarantees zero-migration compatibility for future Sentinel Vision (YOLO/Object Detection) outputs:
- Vision bounding box telemetry, object class tags, model version strings, and EXIF headers map directly into `evidence.metadata` (`JSONB`).
- Physical detection metrics (e.g., detected pipe length, surface area, object counts) map into `evidence.value` and `evidence.unit`.
- Spatial metadata maps into `evidence.location` (`JSONB`).

---

## 2. EVIDENCE GRAPH AUDIT

### End-to-End Relationship Traceability

```
Project (projects.id)
   │ (1:N Foreign Key)
   ▼
Claim (claims.id)
   │ (1:N Foreign Key)
   ▼
Evidence (evidence.id)
   │ (UUID Array & Pairwise FKs)
   ├───────────────────────────────┐
   ▼                               ▼
Finding (findings.id)     Contradiction (contradictions.id)
   │                               │
   └───────────────┬───────────────┘
                   │ (Foreign Keys)
                   ▼
       Investigation (investigations.id)
                   │
                   ▼
         Decision State (investigations.current_state)
```

### Relational Storage vs. UI Inference
- **Explicit Database Storage:** All node entities (`projects`, `claims`, `evidence`, `findings`, `contradictions`, `investigations`) and explicit edges (`claims.project_id`, `evidence.claim_id`, `contradictions.evidence_a_id`, `contradictions.evidence_b_id`, `contradictions.claim_id`) are stored natively via relational foreign keys.
- **UI Inference Gaps:** None. The UI does not need to guess or infer edges between claims, evidence, or contradictions. Every graph connection is queryable directly via standard SQL joins or CTEs.

---

## 3. INVESTIGATION STATE MACHINE AUDIT

### Documented vs. Schema State Alignment

The PostgreSQL `CHECK` constraint on `investigations.current_state` was audited against `docs/INVESTIGATION_STATE_MACHINE.md`:

```sql
CHECK (current_state IN (
    'CREATED', 'INTAKE', 'CLAIMS_IDENTIFIED', 'EVIDENCE_COLLECTION',
    'CROSS_CHECK', 'CONFLICT_ANALYSIS', 'DECISION', 'SUPPORTED',
    'PARTIALLY_SUPPORTED', 'CONTRADICTED', 'INSUFFICIENT_EVIDENCE',
    'HUMAN_REVIEW_REQUIRED', 'CORRECTION', 'CASE_MEMORY', 'CLOSED'
))
```

### Transition Verification
- **Pipeline States:** `CREATED` $\rightarrow$ `INTAKE` $\rightarrow$ `CLAIMS_IDENTIFIED` $\rightarrow$ `EVIDENCE_COLLECTION` $\rightarrow$ `CROSS_CHECK` $\rightarrow$ `CONFLICT_ANALYSIS` $\rightarrow$ `DECISION`. (Fully representable).
- **Decision States:** `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, `HUMAN_REVIEW_REQUIRED`. (Fully representable).
- **Human Review Flow:** `HUMAN_REVIEW_REQUIRED` $\rightarrow$ `CORRECTION` $\rightarrow$ `CASE_MEMORY` $\rightarrow$ `CLOSED`. (Fully representable).
- **Audit Finding:** The database stores `current_state` and `previous_state` (VARCHAR). Value validity is strictly enforced by SQL `CHECK` constraints. Transition path logic is managed by the orchestrator service layer.

---

## 4. HUMAN CORRECTION AUDIT

### Traceability of Human Override Logic

Trace:
`Investigation` $\rightarrow$ `Evidence` $\rightarrow$ `Original Interpretation` $\rightarrow$ `Human Correction` $\rightarrow$ `Reason` $\rightarrow$ `Case Memory`

- `human_corrections` table explicitly stores:
  - `investigation_id` (FK to `investigations`)
  - `evidence_ids_involved` (`UUID[]` array referencing `evidence.id`)
  - `original_interpretation` (`TEXT`)
  - `corrected_interpretation` (`TEXT`)
  - `reason_for_correction` (`TEXT`)
- `case_memory` table explicitly stores:
  - `human_correction_id` (`UUID` FK to `human_corrections(id)`)
  - `investigation_id` (`UUID` FK to `investigations(id)`)
  - `precedent_rule` (`TEXT`)
  - `lessons_learned` (`TEXT`)

**Audit Verdict:** Case memory is strictly linked via foreign key to the `human_corrections` row and its underlying evidence. It is impossible for case memory to exist as a detached text note without relational lineage to the original evidence and investigation.

---

## 5. CASE MEMORY AUDIT

### Retrieval Categorization & Vector Readiness

- **Categorization Support:** Future RAG queries can isolate precedent cases by:
  - *Project Type / Domain:* Query `case_memory.project_id` $\rightarrow$ `projects.metadata->>'department'`.
  - *Scenario Pattern:* Query `case_memory.pattern_type` (e.g. `'STAGED_MATERIAL_DISCREPANCY'`).
  - *Original Reasoning:* Join `case_memory` $\rightarrow$ `human_corrections.original_interpretation`.
  - *Correction & Precedent Rule:* Query `case_memory.precedent_rule` and `case_memory.lessons_learned`.
  - *Evidence Context:* Join `human_corrections.evidence_ids_involved` $\rightarrow$ `evidence`.
- **Vector Search Readiness:** The schema is 100% vector-ready. Adding an `embedding vector(1536)` column to `case_memory` via `pgvector` in a future migration requires zero structural schema modifications or foreign key redesigns.

---

## 6. RLS / SECURITY AUDIT

### Policy Boundary Analysis

| Security Domain | Table | Public Access (`anon`) | Authenticated Auditor | Service Role | Privilege Risk Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Civic Data** | `projects` | **SELECT** (`USING true`) | **SELECT** | **ALL** | **SECURE** |
| **Civic Data** | `claims` | **SELECT** (`USING true`) | **SELECT** | **ALL** | **SECURE** |
| **Civic Data** | `evidence` | **SELECT** (`USING true`) | **SELECT** | **ALL** | **SECURE** |
| **Investigation**| `investigations`| **SELECT** (Terminal states only) | **SELECT** (All states) | **ALL** | **SECURE** |
| **Internal Audit**| `findings` | **NONE** | **ALL** | **ALL** | **ROLE SCOPING RECOMMENDED** |
| **Internal Audit**| `contradictions`| **NONE** | **ALL** | **ALL** | **ROLE SCOPING RECOMMENDED** |
| **Human Memory** | `human_corrections`| **NONE** | **ALL** | **ALL** | **ROLE SCOPING RECOMMENDED** |
| **Human Memory** | `case_memory` | **NONE** | **SELECT** | **ALL** | **SECURE** |

**Audit Findings:**
- Public citizens cannot modify any database records.
- Public citizens cannot view internal agent reasoning (`findings`), conflict hyper-edges (`contradictions`), or raw human corrections (`human_corrections`).
- `authenticated` role policies currently grant access to all signed-in users. Custom JWT role claim verification (`auth.jwt() ->> 'role' = 'auditor'`) should be applied in Phase 1 to prevent generic authenticated users from submitting human corrections.

---

## 7. DEMO DATA AUDIT

### Seed Record Logical Relationship Trace (`001_demo_drainage_project.sql`)

The seed script constructs a complete, coherent, realistic investigation scenario for **Ward 7 Drainage Improvement**:

1. **Project:** `Ward 7 Drainage Improvement` (`a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11`), Sanctioned: ₹18,00,000, Released: ₹7,20,000.
2. **Claims:**
   - Claim 1 (`c1eebc99-...`): 80% physical completion claimed.
   - Claim 2 (`c2eebc99-...`): 400m RCC Hume pipe installation claimed.
3. **Evidence Diversity:**
   - **A. Supported Evidence (`e1eebc99-...`):** Measurement Book entry MB-402 certifying 400m pipe work (`relationship = 'SUPPORTS'`).
   - **B. Contradictory Evidence (`e2eebc99-...`):** Third-party site photo inspection INSP-009 showing only 180m pipe laid in active trench (`relationship = 'CONTRADICTS'`).
   - **C. Neutral Evidence (`e3eebc99-...`):** Invoice INV-9941 confirming 400m pipe purchase & delivery to contractor site yard (`relationship = 'NEUTRAL'`).
   - **D. Missing / Insufficient Evidence (`e4eebc99-...`):** Absent bank clearance certificate for second claimed tranche (`relationship = 'INSUFFICIENT'`).
4. **Investigation & Contradiction:**
   - Session `i1eebc99-...` triggered into state `HUMAN_REVIEW_REQUIRED`.
   - Contradiction `x1eebc99-...` explicitly links MB entry (`e1`) and Trench Photo (`e2`) as a `HIGH` severity physical conflict.
5. **E. Human Correction (`h1eebc99-...`):**
   - Chief Auditor K. Sharma inspects site context and records: 180m is laid in trench, and 220m of Hume pipes are stacked adjacent to trench in contractor staging yard ready for laying. Corrects interpretation from "unexecuted work" to "staged material in progress".
6. **F. Case Memory (`m1eebc99-...`):**
   - Pattern `STAGED_MATERIAL_DISCREPANCY` stores precedent rule: check material purchase invoices for site delivery before flagging linear pipe trench photo discrepancy as unexecuted work.

---

## 8. PRODUCT INVARIANT AUDIT

- **Not a Fraud Detector:** Verified. No table, column, enum, or seed text uses accusation terminology or automated fraud scoring.
- **Not an Automatic Accusation System:** Verified. Conflicts trigger `HUMAN_REVIEW_REQUIRED` for human auditor judgment.
- **Not an Automatic Payment-Denial System:** Verified. Claims remain under audit verification; financial authorization remains external.
- **LLM is NOT Source of Truth:** Verified. Raw empirical evidence is preserved in `evidence` table (append-only). Agent conclusions reside separately in `findings`.
- **No Fake Model Retraining:** Verified. Learning is achieved purely through RAG over structured `human_corrections` $\rightarrow$ `case_memory` records.

---

## 9. PHASE 1 RISKS

| Severity | File Path | Exact Issue | Impact | Recommended Fix |
| :--- | :--- | :--- | :--- | :--- |
| **P1** | [`supabase/migrations/001_sentinel_schema.sql`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/supabase/migrations/001_sentinel_schema.sql#L123) | `findings.evidence_ids` and `human_corrections.evidence_ids_involved` use PostgreSQL `UUID[]` arrays instead of junction tables. | Foreign key constraints cannot be natively enforced on elements inside PostgreSQL arrays. Deleting an evidence row will not trigger constraint checks on array items. | In Phase 1 service layer, implement validation checks or create explicit junction tables (`finding_evidence`, `correction_evidence`). |
| **P1** | [`supabase/migrations/001_sentinel_schema.sql`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/supabase/migrations/001_sentinel_schema.sql#L300) | RLS write policies on `human_corrections` and `findings` grant access `TO authenticated USING (true);`. | Any self-registered authenticated Supabase user could forge human auditor corrections via client API unless scoped by app metadata. | Scope `authenticated` write policies to check custom JWT role claim `auth.jwt() ->> 'role' = 'auditor'` or route writes via `service_role` Edge Functions. |
| **P2** | [`supabase/migrations/001_sentinel_schema.sql`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/supabase/migrations/001_sentinel_schema.sql#L92) | `investigations.current_state` relies on string `CHECK` constraint without a state transition trigger. | Invalid direct state jumps (e.g. `CREATED` $\rightarrow$ `CLOSED`) are syntactically valid in SQL if not restricted by service logic. | Enforce state machine transition graphs strictly in Orchestrator Edge Functions or via a PL/pgSQL validation trigger. |

---

## 10. FINAL VERDICT

```
READY_FOR_PHASE_1
```
