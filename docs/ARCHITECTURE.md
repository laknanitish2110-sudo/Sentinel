# SENTINEL: System Architecture
## Technical Design & Infrastructure Specification

> **Version:** 0.1.0 (Phase 0 - Foundation)  
> **Stack:** Supabase PostgreSQL | Supabase Edge Functions | Claude API  

---

## 1. System Overview & Minimal Topology

Sentinel adopts a lean, serverless-native architecture designed to eliminate unnecessary operational complexity. It deliberately avoids heavy microservice frameworks, external task queues (e.g., Redis, ARQ), or graph databases (e.g., Neo4j), relying instead on **Supabase PostgreSQL** as the single source of truth and execution state core.

```
+-----------------------------------------------------------------------+
|                            USER INTERFACE                             |
|          +-----------------------+     +-----------------------+      |
|          |   Citizen Transparency|     | Auditor / Inspector   |      |
|          |     Portal (Public)   |     |    Portal (Auth)      |      |
|          +-----------+-----------+     +-----------+-----------+      |
+----------------------|-----------------------------|------------------+
                       |                             |
                       | REST / Realtime             | Authenticated REST
                       v                             v
+-----------------------------------------------------------------------+
|                        SUPABASE / POSTGRES CORE                       |
|                                                                       |
|   +-------------------+  +-------------------+  +-----------------+   |
|   |  Projects & Claims|  | Normalized        |  | Investigations, |   |
|   |  (Public Schema)  |  | Evidence Contract |  | Findings &      |   |
|   +-------------------+  +-------------------+  | Contradictions  |   |
|                                                 +--------+--------+   |
|   +-------------------+  +-------------------+           |            |
|   | Human Corrections |  | Precedent Case    |           |            |
|   | (Audit Trail)     |  | Memory (RAG)      |           |            |
|   +-------------------+  +-------------------+           |            |
|                                                          |            |
|                    Row Level Security (RLS)              |            |
+----------------------------------------------------------|------------+
                                                           |
                                                           v
+-----------------------------------------------------------------------+
|                    AGENTIC ORCHESTRATION LAYER                        |
|                                                                       |
|   +---------------------------------------------------------------+   |
|   |               Investigation Orchestrator                      |   |
|   |  (Supabase Edge Function / Node Execution via Claude API)     |   |
|   +---------+--------------------+--------------------+-----------+   |
|             |                    |                    |               |
|   +---------v-------+  +---------v-------+  +---------v-------+       |
|   | Evidence Intake |  | Financial Cross |  | Historical      |       |
|   | Agent           |  | Check Agent     |  | Context Agent   |       |
|   +-----------------+  +-----------------+  +-----------------+       |
+-----------------------------------------------------------------------+
```

---

## 2. Core Architectural Principles

1. **Relational Core for Relational Integrity:**  
   Financial claims, physical evidence, investigation states, and human corrections have strict relational links. Postgres foreign keys enforce referential integrity across the entire investigation lifecycle.

2. **JSONB for Varied Payloads:**  
   Strict fields (`evidence_id`, `project_id`, `value`, `unit`, `confidence`, `reliability`, `relationship`) are stored in structured columns. Dynamic metadata (e.g., EXIF telemetry, camera sensor IDs, raw OCR extraction JSON, bounding box vectors) is isolated within `JSONB` columns.

3. **Deterministic State Transitions:**  
   Investigation state logic is enforced by Postgres database constraints and orchestrator state machine rules. LLMs can recommend findings, but state transitions follow deterministic code paths.

4. **Auditable Invariance:**  
   Raw evidence rows are append-only. When a human auditor corrects an investigation, the original evidence and original findings remain untouched; a `human_corrections` record is appended, creating a transparent, unalterable audit log.

---

## 3. Data Flow Architecture

```
   Raw Input (Document, Photo, Bill)
                 |
                 v
   +---------------------------+
   |   Evidence Intake Agent   | ---> Normalizes into Evidence Contract
   +-------------+-------------+
                 |
                 v
   +---------------------------+
   |   Database Insertion      | ---> Saved in `evidence` table
   +-------------+-------------+
                 |
                 v
   +---------------------------+
   |  Financial Cross-Check    | ---> Checks `claims` vs `evidence`
   +-------------+-------------+
                 |
                 v
   +---------------------------+
   | Historical Context Lookup | ---> Queries `case_memory` for past precedents
   +-------------+-------------+
                 |
                 v
   +---------------------------+
   | Conflict & State Engine   | ---> Populates `findings` & `contradictions`
   +-------------+-------------+
                 |
                 v
   +---------------------------+
   | Orchestrator Decision     | ---> Sets state: `SUPPORTED`, `CONTRADICTED`,
   +-------------+-------------+      or `HUMAN_REVIEW_REQUIRED`
                 |
                 v (If Review Required)
   +---------------------------+
   | Human Auditor Review      | ---> Inserts `human_corrections`
   +-------------+-------------+
                 |
                 v
   +---------------------------+
   | Case Memory Generation    | ---> Appends to `case_memory` for future investigations
   +---------------------------+
```

---

## 4. Security Architecture & Row Level Security (RLS)

Sentinel uses Supabase RLS to strictly separate public civic data from sensitive internal investigation and auditor workflow data.

### Security Domains:

| Table | RLS Policy Strategy | Target Audience |
| :--- | :--- | :--- |
| `projects` | **Public Read** (`anon`, `authenticated`), **Write Restricted** to system service role. | Citizens, Auditors, Public |
| `claims` | **Public Read** (`anon`, `authenticated`), **Write Restricted** to system service role. | Citizens, Auditors, Public |
| `evidence` | **Public Read** (`anon`, `authenticated`), **Write Restricted** to system service role. | Citizens, Auditors, Public |
| `investigations` | **Public Read** for state summary, **Detailed Execution Log Restricted** to `authenticated` investigators. | Auditors & System Orchestrator |
| `findings` | **Restricted Read/Write** to `authenticated` investigators and system service role. | Auditors & System Orchestrator |
| `contradictions` | **Restricted Read/Write** to `authenticated` investigators and system service role. | Auditors & System Orchestrator |
| `human_corrections` | **Restricted Read/Write** to `authenticated` investigators. | Auditors |
| `case_memory` | **Restricted Read/Write** to `authenticated` investigators and system service role. | Agents & Auditors |

---

## 5. Evidence Graph in Relational Postgres

Rather than deploying a separate graph database, Sentinel represents the **Evidence Graph** natively in Postgres using normalized relational tables:

- **Nodes:**  
  - `claims` (Nodes representing contractor assertions)
  - `evidence` (Nodes representing physical/financial observations)
- **Edges:**  
  - `evidence.claim_id` establishes directional edges from Evidence -> Claim.
  - `evidence.relationship` defines the edge semantics (`SUPPORTS`, `CONTRADICTS`, `NEUTRAL`, `INSUFFICIENT`).
  - `contradictions` table stores explicit conflict hyper-edges connecting pair-wise conflicting evidence items (`evidence_a_id` <--> `evidence_b_id`) under a specific claim and investigation.

This allows graph traversals (e.g., finding all evidence contradicting Claim X, or finding conflicting evidence clusters) using standard SQL queries and Recursive Common Table Expressions (CTEs).

---

## 6. Vision & MCP Extensibility Strategy

While Vision (YOLO/Object Detection) and Model Context Protocol (MCP) are deferred for Phase 0:

- **Vision Readiness:**  
  The `evidence` table includes `location` (coordinates/text), `confidence` (numeric), `reliability` (numeric/enum), and `metadata` (JSONB). Future vision model outputs (e.g. bounding box coordinates, detected pipe counts, surface area estimations) map directly into `evidence.metadata` without requiring schema migrations.
- **MCP Readiness:**  
  The agent boundary interfaces (Intake, Cross-Check, Historical Context) are designed as isolated, functional tools with clean input/output JSON schemas, enabling frictionless wrapping into MCP tool specifications when required.
