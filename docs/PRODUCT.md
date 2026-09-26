# SENTINEL: Agentic Evidence Intelligence System
## Product Specification & Vision

> **Version:** 0.1.0 (Phase 0 - Foundation)  
> **Status:** Architecture & Schema Specification  
> **Target System:** Public Infrastructure Fund Utilization Tracking  

---

## 1. Executive Summary

**SENTINEL** is an Agentic Evidence Intelligence system built to bring absolute, verifiable transparency to public infrastructure projects. Public infrastructure investments frequently suffer from information opacity, discrepancy between physical progress and financial disbursements, and a lack of auditability. 

Sentinel bridges this gap by ingesting multi-source physical and financial evidence, evaluating claims against empirical data, tracking discrepancies, and learning systematically from human expert feedback without risking silent LLM hallucinations or unauthorized record modification.

---

## 2. Core Questions Answered

Sentinel operates with a singular focus on answering three fundamental questions for any public work project:

1. **Where did the money go?**  
   *Financial Traceability:* Mapping sanctioned funds to released tranches, contractor invoices, measurement book (MB) records, bank disbursements, and line-item expenditures.

2. **Does the evidence support what is being claimed?**  
   *Evidence Verification:* Cross-referencing contractor completion claims (e.g., "80% complete", "400m drainage pipe installed") against physical inspection notes, geotagged evidence, measurement logs, and material supply bills.

3. **Did Sentinel learn from the last time a human corrected it?**  
   *Institutional Memory:* Storing structured human corrections as precedent case memory so future agent investigations inherit past auditor insights and domain context without requiring model retraining.

---

## 3. Product Boundaries & Non-Goals

To maintain legal integrity, technical rigor, and public trust, Sentinel operates under strict product boundaries:

| Boundary | Description & Invariant |
| :--- | :--- |
| **NOT a Fraud Detector** | Sentinel does **NEVER** automatically accuse a contractor, engineer, or official of fraud or illegal activity. Sentinel highlights *evidentiary discrepancies* and *gaps*. Accusation remains strictly a human legal/administrative decision. |
| **Evidence vs. Claims** | Sentinel treats contractor statements, completion certificates, and billing requests strictly as **Claims**, never as evidence. Evidence consists solely of empirical observations (photos, bank statements, third-party physical inspections). |
| **Uncertainty vs. Contradiction** | Missing data is **NEVER** classified as contradiction. If evidence is lacking, Sentinel marks the state as `INSUFFICIENT_EVIDENCE`. Contradiction requires explicit conflicting evidence (`SUPPORTS` vs `CONTRADICTS`). |
| **Database is Source of Truth** | LLMs perform reasoning over structured evidence snapshots. LLMs **CANNOT** directly write, alter, or delete database rows. Database mutations occur strictly through validated system pipelines or human review actions. |
| **First-Class Human Correction** | Human auditor overrides are not simple UI edits—they produce structured `human_corrections` and `case_memory` records that directly feed future agent context windows. |
| **No Fake Model Retraining** | Sentinel does not claim to perform "live fine-tuning" or "on-the-fly model retraining". Learning is achieved via structured retrieval of RAG-based precedent cases (`case_memory`) during context formulation. |

---

## 4. Primary Stakeholders & Target Users

1. **Municipal / Government Auditors:**  
   Review project claims, view multi-agent synthesis summaries, resolve flagged evidence contradictions, and input authoritative human corrections.
2. **Civic Oversight Bodies & Journalists:**  
   Track project status, examine public evidence contracts, inspect disbursement-vs-physical work alignment.
3. **Citizens & Community Members:**  
   Access transparent, citizen-readable project timelines, physical evidence logs, and verified claim statuses.

---

## 5. MVP Agent Architecture Overview

Sentinel orchestrates three specialized sub-agents managed by a central **Investigation Orchestrator**:

```
                  +-------------------------------+
                  |   Investigation Orchestrator  |
                  +---------------+---------------+
                                  |
        +-------------------------+-------------------------+
        |                         |                         |
+-------v-------+       +---------v---------+       +-------v-------+
|  1. Evidence  |       |   2. Financial    |       | 3. Historical |
| Intake Agent  |       | Cross-Check Agent |       | Context Agent |
+---------------+       +-------------------+       +---------------+
```

1. **Evidence Intake Agent:**  
   Ingests raw documents, physical inspection reports, bills, geotagged entries, and normalizes them into the **Evidence Contract**.
2. **Financial Cross-Check Agent:**  
   Compares financial releases, sanctioned budgets, line-item invoices, and Measurement Book (MB) records to detect financial variance or unaccounted allocations.
3. **Historical Context Agent:**  
   Retrieves structured `case_memory` from previous human corrections across similar projects, wards, or contractor patterns to inform current conflict analysis.
4. **Investigation Orchestrator:**  
   Enforces the **Investigation State Machine**, coordinates agent workflow, aggregates agent findings, evaluates conflict severity, and transitions investigations into decision or review states.

---

## 6. Scope Roadmap

* **Phase 0 (Current Foundation):** Core schema design, Evidence Contract specification, State Machine design, security architecture (RLS), and reproducible demo seed data. No active agents or frontend.
* **Phase 1 (Core Agents & Pipeline):** Orchestrator execution engine, Supabase integration, Claude API tool-calling for intake, cross-check, and historical RAG lookup.
* **Phase 2 (Evidence Graph & Vision Readiness):** Image observation extraction, bounding box metadata support in Evidence Contract, graph-based contradiction traversal.
* **Phase 3 (Public Dashboard & Audit Interface):** Citizen-facing transparency UI, Auditor Correction Portal, and Case Memory feedback loops.
