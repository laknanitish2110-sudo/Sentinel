# SENTINEL

**Public Infrastructure Accountability System**

Sentinel cross-checks government infrastructure claims against multiple independent evidence sources — official records, site inspections, financial documents, and photos. When the evidence doesn't match, it flags the discrepancy so auditors and citizens can act.

Built for **Prompthon AI Edition 2026** — Problem Statement #504: Public Fund Utilization Tracker.

---

## Screenshots

### Landing & Project Overview
![Hero](docs/screenshots/01_hero.png)
*"Where is your tax money going?" — Select an infrastructure project and see its budget, release, and claim figures at a glance.*

### Follow the Money
![Money Trail](docs/screenshots/02_money_trail.png)
*Track sanctioned budget → funds released → contractor claim. The amber callout flags when the numbers don't add up.*

### Does the Evidence Match the Claim?
![Evidence Graph](docs/screenshots/03_evidence_graph.png)
*The contractor's claim is checked against 5 independent sources. Each card shows what that source says, its reliability rating, and whether it supports or contradicts the claim.*

### Watch the AI Investigate
![Agent Trace](docs/screenshots/04_agent_trace.png)
*The agentic investigation loop dynamically decides what to check next — not a fixed script. Every reasoning step is visible.*

### Plain-Language Explanation & Auditor Override
![Explanation](docs/screenshots/05_explanation.png)
*Evidence-grounded findings in plain language. Auditors can submit corrections, and Sentinel learns from them for future investigations.*

---

## The Problem

In India's public infrastructure spending (over ₹10 lakh crore annually), there's a fundamental information asymmetry: contractors claim work is done, officials certify it, money flows — but citizens have no way to verify whether the road was actually built, the drain was actually laid, or the bridge actually stands.

Existing systems like OMMAS and PMGSY track project metadata (milestones, budgets, dates) but don't cross-verify the actual physical evidence against financial claims. A contractor can file a Measurement Book entry for 400m of pipe while only 180m is visible on-site, and no system catches the discrepancy automatically.

## What Sentinel Does

Sentinel answers three questions for any public infrastructure project:

1. **Where did the money go?** — Maps sanctioned funds → released tranches → contractor claims → bank disbursements
2. **Does the evidence support what's claimed?** — Cross-references contractor claims against physical inspections, geotagged photos, invoices, MB records, and bank statements
3. **Did it learn from past corrections?** — Stores structured auditor corrections as case memory, so the same mistake isn't repeated

## Who It's For

| User | What They Get |
|------|---------------|
| **Citizens** | Transparent dashboard showing where tax money went, evidence for/against claims, plain-language verdicts. Enough data to file an RTI if something looks wrong. |
| **Government Auditors** | Multi-source evidence synthesis, automated discrepancy detection, correction interface that feeds future investigations. |
| **Civic Journalists & NGOs** | Structured evidence trails, reliability-rated sources, exportable investigation summaries. |

---

## Architecture

```
                    ┌─────────────────────────────┐
                    │     Citizen Dashboard        │
                    │  (HTML/CSS/JS — Single Page)  │
                    └──────────────┬──────────────┘
                                   │ REST API
                                   ▼
                    ┌─────────────────────────────┐
                    │      Sentinel API Layer      │
                    │   (api.py — Role-Based ACL)  │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
   ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
   │   Orchestrator    │ │  Agent Loop      │ │   Validator      │
   │  14-State Machine │ │  Dynamic Planner │ │  Safety Rules    │
   └────────┬─────────┘ └────────┬─────────┘ └──────────────────┘
            │                    │
            ▼                    ▼
   ┌──────────────────────────────────────────┐
   │           6 Investigation Tools          │
   │                                          │
   │  analyze_photo    cross_check_values     │
   │  verify_financial_trail                  │
   │  search_precedents  flag_discrepancy     │
   │  request_human_review                    │
   └────────────────────┬─────────────────────┘
                        │
                        ▼
   ┌──────────────────────────────────────────┐
   │          SQLite + Evidence Contract       │
   │                                          │
   │  Projects │ Claims │ Evidence │ Findings │
   │  Human Corrections │ Case Memory         │
   └──────────────────────────────────────────┘
```

### Key Design Decisions

- **14-State Investigation Machine** (`orchestrator.py`): Deterministic state transitions ensure investigations follow auditable paths. LLMs reason over evidence but cannot skip states or bypass human review.

- **Agentic Investigation Loop** (`agent_loop.py`): A dynamic planner (`_decide_next_action`) chooses which tool to call next based on what's been found so far — not a fixed pipeline. Supports Claude API mode and a deterministic fallback.

- **Evidence Contract** (`types.py`): Every evidence item, regardless of source, conforms to a universal interface with `source_type`, `value`, `unit`, `confidence`, `reliability`, and `relationship` fields. This makes cross-source comparison possible.

- **Non-Accusatory Safety Design** (`validator.py`): Sentinel never accuses anyone of fraud. It highlights evidentiary discrepancies and gaps. Forbidden terms are enforced at the output layer.

- **Case Memory / Institutional Learning** (`db.py`): When a human auditor corrects Sentinel, the correction is stored as a structured precedent. Future investigations retrieve relevant precedents to avoid repeating the same error.

- **Dual-Mode Execution**: Claude API for full agentic reasoning when available; deterministic fallback (pairwise evidence comparison, rule-based decisions) when it's not — same investigation quality, no API dependency for core logic.

### Investigation States

```
CREATED → INTAKE → CLAIMS_IDENTIFIED → EVIDENCE_COLLECTION → CROSS_CHECK
→ CONFLICT_ANALYSIS → DECISION → { SUPPORTED | CONTRADICTED | INSUFFICIENT_EVIDENCE }
→ HUMAN_REVIEW_REQUIRED → CORRECTION_APPLIED → LEARNING_STORED → CLOSED
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11, SQLite (in-memory for demo) |
| **AI** | Claude Sonnet 4 API (agentic loop) + deterministic fallback |
| **Vision** | PIL/Pillow (edge density, color statistics, construction detection) |
| **Frontend** | Vanilla HTML/CSS/JS (single-page app, no framework) |
| **Deployment** | Vercel Serverless Functions |
| **Testing** | pytest (134 tests across all modules) |

---

## Project Structure

```
sentinel/
├── src/sentinel/
│   ├── agent_loop.py       # Agentic investigation with dynamic planner
│   ├── api.py              # REST API with role-based access control
│   ├── claude_client.py    # Claude API integration
│   ├── db.py               # SQLite database + case memory storage
│   ├── orchestrator.py     # 14-state investigation state machine
│   ├── types.py            # Evidence Contract (universal data types)
│   └── validator.py        # Safety rules + forbidden term enforcement
├── public/
│   ├── index.html          # Citizen dashboard
│   ├── styles.css          # UI styles
│   └── app.js              # Frontend logic (API calls, rendering)
├── api/
│   └── index.py            # Vercel serverless entry point
├── tests/                  # 134 tests across all phases
├── docs/                   # Architecture, product spec, state machine docs
└── vercel.json             # Deployment config
```

---

## Use Cases

### 1. Citizen Oversight
A resident in Ward 7 sees that ₹18L was sanctioned for storm drain construction. The dashboard shows only ₹7.2L was released but the contractor claims ₹14.4L of work done. The evidence graph reveals that physical inspection found only 180m of the claimed 400m. The citizen now has enough documented evidence to file an RTI or raise the issue at a ward meeting.

### 2. Auditor Investigation
A government auditor runs an AI investigation on a flagged project. Sentinel's agent cross-checks MB records against site photos, compares invoice quantities with delivery records, and flags a 55% discrepancy between certified and visible work. The auditor reviews the finding, realizes the pipe work is underground (backfilled), submits a correction with excavation log evidence. Sentinel stores this as case memory — next time it encounters subsurface infrastructure, it checks backfilling logs before concluding work wasn't done.

### 3. Pattern Detection Across Projects
After processing multiple ward projects, Sentinel's case memory accumulates patterns: "STAGED_MATERIAL_DISCREPANCY" (materials delivered to site but not installed), "SUBSURFACE_INFRASTRUCTURE" (underground work invisible to surface inspection), "SPLIT_INVOICE_INFLATION" (multiple invoices for the same delivery). Future investigations automatically surface relevant precedents.

### 4. Collusion Resistance
Even if a contractor and Junior Engineer collude to fake MB records, Sentinel cross-checks against independent sources they can't easily control: bank statements (treasury records), geotagged photos (GPS metadata), supplier invoices (third-party), and physical inspections (separate agency). Faking all sources simultaneously requires compromising multiple independent institutions.

---

## Quick Start

```bash
# Clone
git clone https://github.com/laknanitish2110-sudo/Sentinel.git
cd Sentinel

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Start local demo server (seeds sample data)
python -c "
from src.sentinel.db import SentinelDB
from src.sentinel.orchestrator import Orchestrator
db = SentinelDB(':memory:')
# See api/index.py for full setup
"
```

---

## How Evidence Trustworthiness Works

Every evidence item carries two scores:

- **Reliability** (HIGH / MEDIUM / LOW): Based on source type. Treasury bank records = HIGH (government-controlled, hard to fake). Physical inspection = MEDIUM (human observer, limited visibility). Geotagged photos = LOW (can be manipulated, limited context).

- **Confidence** (0.0 - 1.0): How precisely this evidence speaks to the specific claim. A bank statement confirming exact disbursement = 0.95. A photo showing "construction activity" without measuring meters = 0.65.

Sentinel never trusts a single source. The evidence graph shows all sources side-by-side, their reliability, and whether they agree or conflict. The verdict comes from weighted cross-comparison, not any single input.

---

## Safety & Ethics

- **Never accuses**: Sentinel flags discrepancies, not fraud. Accusation is a human legal decision.
- **Uncertainty is preserved**: Missing data = "INSUFFICIENT_EVIDENCE", never "CONTRADICTED".
- **Human override is first-class**: Auditor corrections are stored alongside original findings, creating a transparent audit trail.
- **No silent hallucination**: Every factual statement in the explanation is traced to a stored evidence item.
- **Append-only evidence**: Raw evidence rows are never modified. Corrections are added as new records.

---

## Hackathon Context

**Prompthon AI Edition 2026** | Problem Statement #504: Public Fund Utilization Tracker

**Codebase**: ~7,500 lines (2,100 Python backend + 2,500 frontend + 2,900 tests)
**Tests**: 134 passing across all modules
**Source modules**: 7 core Python modules + Vercel serverless entry

---

## License

MIT
