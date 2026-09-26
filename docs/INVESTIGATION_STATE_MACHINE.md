# SENTINEL: Investigation State Machine
## Lifecycle & Transition Specification

> **Version:** 0.1.0 (Phase 0 - Foundation)  
> **Core Objective:** Formalize deterministic investigation transitions, decision criteria, and human correction feedback loops.

---

## 1. Overview & Core Invariants

The **Investigation State Machine** governs how Sentinel processes a public infrastructure investigation from initial trigger to final closure. It guarantees that multi-agent reasoning proceeds along predictable paths and that all conflicts or uncertainties are escalated appropriately.

### Mandatory Invariants:

1. **Uncertainty Principle:**  
   The orchestrator must **NEVER** convert uncertainty into certainty. Missing data or unverified sources must yield `INSUFFICIENT_EVIDENCE` or `HUMAN_REVIEW_REQUIRED`, never `SUPPORTED` or `CONTRADICTED`.

2. **Contradiction vs. Gap Distinction:**  
   A claim is marked `CONTRADICTED` only when there is explicit, verified evidence with relationship `CONTRADICTS`. If evidence is simply missing (e.g. absent bank voucher), it is an evidentiary gap resulting in `INSUFFICIENT_EVIDENCE`.

3. **Human Review Escalation:**  
   When agents encounter conflicting high-reliability evidence (e.g., MB entry vs Physical Photo), the orchestrator MUST transition to `HUMAN_REVIEW_REQUIRED`. Agents cannot arbitrarily resolve severe contradictions without human review.

---

## 2. Complete State Machine Diagram

```
[CREATED]
   |
   v
[INTAKE] -------------------------> Raw Evidence & Document Ingestion
   |
   v
[CLAIMS_IDENTIFIED] --------------> Contractor Claims Parsed & Registered
   |
   v
[EVIDENCE_COLLECTION] ------------> Evidence Mapped to Claims via Contract
   |
   v
[CROSS_CHECK] --------------------> Financial vs Physical Cross-Check Executed
   |
   v
[CONFLICT_ANALYSIS] --------------> Evidence Graph Evaluated for Contradictions
   |
   v
[DECISION]
   |
   +---> [SUPPORTED] ---------------> All claims corroborated by high-reliability evidence
   |
   +---> [PARTIALLY_SUPPORTED] ------> Subset of claims verified; minor gaps exist
   |
   +---> [CONTRADICTED] ------------> Clear empirical evidence directly refutes claims
   |
   +---> [INSUFFICIENT_EVIDENCE] ---> Critical evidence missing; cannot draw conclusion
   |
   +---> [HUMAN_REVIEW_REQUIRED] ---> Unresolved conflict / high variance detected
            |
            v
         [CORRECTION] --------------> Human Auditor enters correction reason & decision
            |
            v
         [CASE_MEMORY] -------------> Structured precedent memory generated & saved
            |
            v
         [CLOSED] ------------------> Investigation concluded with human precedent stored
```

---

## 3. State Definitions & Transition Matrix

### Pipeline States

| State | Role & Trigger | Next Allowed States |
| :--- | :--- | :--- |
| `CREATED` | Investigation initialized for project. | `INTAKE` |
| `INTAKE` | Evidence Intake Agent processes raw files into Evidence Contract. | `CLAIMS_IDENTIFIED` |
| `CLAIMS_IDENTIFIED` | Contractor claims identified, extracted, and stored in `claims`. | `EVIDENCE_COLLECTION` |
| `EVIDENCE_COLLECTION` | Evidence items linked to specific `claim_id` records. | `CROSS_CHECK` |
| `CROSS_CHECK` | Financial Cross-Check Agent analyzes disbursements vs MB entries vs Invoices. | `CONFLICT_ANALYSIS` |
| `CONFLICT_ANALYSIS` | Historical Context Agent retrieves case memory; contradictions identified. | `DECISION` |
| `DECISION` | Orchestrator evaluates accumulated findings against decision rules. | `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, `HUMAN_REVIEW_REQUIRED` |

### Terminal & Review States

| State | Condition & Outcome |
| :--- | :--- |
| `SUPPORTED` | `>90%` claims corroborated by `HIGH` reliability evidence, 0 severe contradictions. |
| `PARTIALLY_SUPPORTED` | Core work verified, but minor unverified claims or value variances exist (<15%). |
| `CONTRADICTED` | Direct contradiction between `HIGH` reliability physical evidence and claims without reasonable doubt. |
| `INSUFFICIENT_EVIDENCE`| Critical evidence sources missing (e.g. missing bank proof or MB record). |
| `HUMAN_REVIEW_REQUIRED`| Conflicting high-reliability evidence, complex site context, or high financial variance (>15%). |

### Human Review Sub-State Flow

```
HUMAN_REVIEW_REQUIRED
   │
   ▼
[Auditor inspects findings & evidence graph]
   │
   ▼
CORRECTION
   │ (Auditor inputs: original interpretation, corrected interpretation, reason, evidence IDs)
   ▼
CASE_MEMORY
   │ (System transforms correction into precedent rule stored in `case_memory`)
   ▼
CLOSED
   │ (Finalized investigation state)
```

---

## 4. Orchestrator Transition Rules (Pseudo-Logic)

```python
def evaluate_orchestrator_decision(investigation_id):
    claims = get_claims_for_investigation(investigation_id)
    evidence = get_evidence_for_investigation(investigation_id)
    contradictions = get_contradictions(investigation_id)
    
    # Rule 1: High severity unresolved contradictions trigger mandatory human review
    if any(c.severity == 'HIGH' for c in contradictions):
        return "HUMAN_REVIEW_REQUIRED"
        
    # Rule 2: Check for missing critical evidence
    if any(e.relationship == 'INSUFFICIENT' for e in evidence) or len(evidence) == 0:
        return "INSUFFICIENT_EVIDENCE"
        
    # Rule 3: Direct strong contradiction
    if any(e.relationship == 'CONTRADICTS' and e.reliability == 'HIGH' for e in evidence):
        return "CONTRADICTED"
        
    # Rule 4: Partial support check
    if any(e.relationship == 'CONTRADICTS' and e.reliability != 'HIGH' for e in evidence):
        return "PARTIALLY_SUPPORTED"
        
    # Rule 5: Fully supported
    if all(e.relationship == 'SUPPORTS' for e in evidence):
        return "SUPPORTED"
        
    return "HUMAN_REVIEW_REQUIRED"
```
