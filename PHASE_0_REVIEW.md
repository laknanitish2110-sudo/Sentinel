# SENTINEL: Phase 0 Completion & Architecture Review

> **System:** SENTINEL — Agentic Evidence Intelligence System  
> **Phase:** 0 (Foundation Specification & Core Schema)  
> **Status:** Phase 0 Successfully Delivered  

---

## 1. Overview of Delivered Phase 0 Artifacts

Phase 0 establishes the theoretical, architectural, database, and operational foundation for Sentinel. The following deliverables have been created in accordance with product boundaries and engineering requirements:

| Artifact Path | Description |
| :--- | :--- |
| [`docs/PRODUCT.md`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/docs/PRODUCT.md) | Product vision, core questions, boundaries (NOT a fraud detector, Database as Source of Truth, Human Correction first-class), and scope roadmap. |
| [`docs/ARCHITECTURE.md`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/docs/ARCHITECTURE.md) | System topology, data flow diagrams, RLS security architecture, relational evidence graph design, and vision/MCP extensibility strategy. |
| [`docs/EVIDENCE_CONTRACT.md`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/docs/EVIDENCE_CONTRACT.md) | Standardized evidence contract specification, relationship taxonomies (`SUPPORTS`, `CONTRADICTS`, `NEUTRAL`, `INSUFFICIENT`), and vision observation JSON payload examples. |
| [`docs/INVESTIGATION_STATE_MACHINE.md`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/docs/INVESTIGATION_STATE_MACHINE.md) | State lifecycle rules (`CREATED` -> `INTAKE` -> `DECISION` -> `HUMAN_REVIEW_REQUIRED` -> `CORRECTION` -> `CASE_MEMORY` -> `CLOSED`), transition matrix, and uncertainty invariants. |
| [`supabase/migrations/001_sentinel_schema.sql`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/supabase/migrations/001_sentinel_schema.sql) | Production-ready Supabase PostgreSQL migration establishing 8 relational tables, foreign key constraints, CHECK enums, performance indexes, automated triggers, and Row Level Security (RLS). |
| [`supabase/seed/001_demo_drainage_project.sql`](file:///c:/Users/Karthik/OneDrive/Desktop/sentinel/supabase/seed/001_demo_drainage_project.sql) | Realistic seed dataset ("Ward 7 Drainage Improvement") demonstrating supported evidence, contradictory site evidence, missing bank vouchers, human auditor correction, and generated case memory. |

---

## 2. Verification Against Phase 0 Requirements

### Database Integrity & Constraint Checklist
- [x] **No Orphan Records:** Foreign keys link `claims`, `evidence`, `investigations`, `findings`, `contradictions`, `human_corrections`, and `case_memory` with `ON DELETE CASCADE` or `ON DELETE SET NULL`.
- [x] **Foreign Key Rigor:** All 8 primary tables maintain explicit referential integrity.
- [x] **Security & RLS Boundaries:** Supabase RLS is enabled on all tables. `projects`, `claims`, and `evidence` are public-readable (citizen transparency). Internal investigation tables (`findings`, `contradictions`, `human_corrections`, `case_memory`) require `authenticated` auditor credentials or `service_role`.
- [x] **Deterministic Seed Data:** `001_demo_drainage_project.sql` provides deterministic UUID keys and cleanly marked DEMO DATA for a ₹18,00,000 drainage project.
- [x] **Future Vision Extensibility:** The Evidence Contract (`evidence` table) accommodates computer vision outputs (e.g. YOLO bounding box telemetry, camera EXIF, geotags) inside `location` and `metadata` JSONB fields without requiring schema redesign.
- [x] **Evidence Graph Capability:** Supports graph traversals via relational foreign keys and `contradictions` edge tables connecting pair-wise evidence nodes (`evidence_a_id` <--> `evidence_b_id`).
- [x] **Human Correction to Case Memory:** `human_corrections` captures original interpretation, corrected interpretation, and reason; `case_memory` stores extracted precedent rules for future RAG retrieval.

---

## 3. Key Architectural Decisions & Rationale

1. **Relational PostgreSQL Core over Graph DB:**  
   Relational SQL with normalized foreign keys and recursive CTEs provides exact transactional integrity, seamless Supabase integration, and zero extra infra complexity compared to external graph databases.
2. **Immutability of Raw Evidence:**  
   Raw evidence records are append-only. Agent findings or human corrections append new rows in `findings` or `human_corrections` rather than overwriting factual evidence.
3. **Structured Case Memory RAG over Model Fine-Tuning:**  
   Instead of claiming "live model fine-tuning" (which is brittle and non-deterministic), Sentinel transforms human corrections into structured precedent rules (`case_memory`) retrieved during subsequent investigation context assembly.

---

## 4. Unresolved Decisions & Open Questions for Phase 1

1. **Vector Embedding Strategy for Case Memory:**  
   *Decision Pending:* Whether to add pgvector (`vector` column in `case_memory`) directly in Postgres or handle vector embeddings externally via Edge Functions / OpenAI/Claude embeddings during Phase 1.
2. **Orchestrator Trigger Execution Model:**  
   *Decision Pending:* Evaluate whether the orchestrator state machine will be driven by Supabase Database Webhooks / Edge Functions vs a lightweight Node.js worker service when starting Phase 1.

---

## 5. Next Steps

Phase 0 foundation is complete. System is fully ready for Phase 1 approval (Agent orchestration implementation & Claude API integration). No UI, agents, or microservices have been built yet.
