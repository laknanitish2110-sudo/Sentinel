# SENTINEL: Evidence Data Contract
## Standardized Schema & Data Contract Specification

> **Version:** 0.1.0 (Phase 0 - Foundation)  
> **Core Objective:** Unified, normalized representation of heterogeneous infrastructure evidence.  

---

## 1. Overview & Architectural Role

The **Evidence Contract** defines the exact shape and invariants that every evidence source—whether a PDF bill, bank statement, drone image, manual physical inspection, or citizen report—must adhere to before entering the Sentinel data core.

It enforces a strict distinction between:
1. **Claims:** Statements made by contractors, authorities, or project managers asserting work completion, expenditure, or progress.
2. **Raw Evidence:** Empirical observations, document records, sensor logs, or physical measurements captured from verified sources.
3. **Agent Findings:** Reasoning outputs, deductions, or synthesis synthesized by LLMs operating *over* evidence.

> [!IMPORTANT]  
> **Rule of Evidence Invariance:**  
> An LLM output or agent reasoning conclusion MUST NEVER be stored directly in the `evidence` table as if it were raw empirical evidence. Agent conclusions belong exclusively in `findings` or `contradictions`.

---

## 2. Core Evidence Schema Specification

Every normalized evidence record must satisfy the following structural contract:

| Field Name | Data Type | Nullable | Description & Constraints |
| :--- | :--- | :--- | :--- |
| `evidence_id` | `UUID` | **No** | Primary Key. Unique identifier for the evidence entry. |
| `project_id` | `UUID` | **No** | Foreign Key referencing `projects(id)`. |
| `claim_id` | `UUID` | **Yes** | Foreign Key referencing `claims(id)`. Null if evidence is project-level. |
| `source_type` | `VARCHAR(50)` | **No** | Categorical source type (e.g., `MB_RECORD`, `INVOICE`, `GEO_PHOTO`, `BANK_STATEMENT`, `PHYSICAL_INSPECTION`, `CITIZEN_REPORT`). |
| `source_id` | `VARCHAR(255)` | **No** | External identifier of the source document/file (e.g. Document #, Storage Path, Transaction ID). |
| `observation` | `TEXT` | **No** | Clear, factual description of what was observed or extracted. |
| `value` | `NUMERIC(15,2)` | **Yes** | Quantitative value associated with the observation (e.g. `180.00`, `720000.00`). |
| `unit` | `VARCHAR(50)` | **Yes** | Unit of measurement for value (e.g., `meters`, `INR`, `percent`, `count`). |
| `timestamp` | `TIMESTAMPTZ` | **Yes** | Time when the evidence was captured, generated, or recorded on-site. |
| `location` | `JSONB` | **Yes** | Structured location (e.g. `{"latitude": 12.9716, "longitude": 77.5946, "address": "Ward 7 Main Trench"}`). |
| `confidence` | `NUMERIC(3,2)` | **No** | Extraction or measurement confidence score between `0.00` and `1.00`. |
| `reliability` | `VARCHAR(20)` | **No** | Reliability rating of the source (`HIGH`, `MEDIUM`, `LOW`, `UNVERIFIED`). |
| `relationship` | `VARCHAR(20)` | **No** | Relationship to target claim: `SUPPORTS`, `CONTRADICTS`, `NEUTRAL`, `INSUFFICIENT`. |
| `metadata` | `JSONB` | **No** | Arbitrary flexible payload (e.g., file hashes, vision bounding boxes, EXIF header). Defaults to `{}`. |
| `created_at` | `TIMESTAMPTZ` | **No** | System ingestion timestamp. Defaults to `NOW()`. |

---

## 3. Relationship Taxonomy & Invariants

Sentinel categorizes every evidence-to-claim relationship into four explicit values:

- **`SUPPORTS`**: The empirical observation directly corroborates the assertion in the claim (e.g., Measurement Book entry verifies 400m pipe laid and physical inspection verifies 400m pipe present).
- **`CONTRADICTS`**: The empirical observation conflicts directly with the claim (e.g., Contractor claims 400m pipe installed; physical site inspection verifies only 180m installed).
- **`NEUTRAL`**: The evidence is relevant to the project/claim but neither proves nor disproves the claim (e.g., An invoice showing 400m of pipe was purchased, which proves material acquisition but not installation).
- **`INSUFFICIENT`**: The evidence is incomplete, unverified, or ambiguous, making it impossible to evaluate support or contradiction (e.g., A blurry photo or un-itemized receipt).

---

## 4. Vision Observation Compatibility

The Evidence Contract is explicitly designed to handle future Computer Vision (YOLO/Object Detection) outputs without schema alterations.

### Example Vision Payload Mapping:

```json
{
  "evidence_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3d0001",
  "project_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "claim_id": "c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22",
  "source_type": "GEO_PHOTO",
  "source_id": "storage://site-photos/ward7_trench_section3.jpg",
  "observation": "Computer vision analysis detected 180 meters of laid hume pipe along trench section 3.",
  "value": 180.00,
  "unit": "meters",
  "timestamp": "2026-09-20T10:30:00Z",
  "location": {
    "latitude": 12.9784,
    "longitude": 77.5921,
    "altitude_m": 920.5
  },
  "confidence": 0.92,
  "reliability": "HIGH",
  "relationship": "CONTRADICTS",
  "metadata": {
    "vision_model": "yolov8-drainage-pipe-v2",
    "bounding_boxes": [
      { "class": "installed_pipe", "confidence": 0.94, "box": [120, 340, 580, 410] },
      { "class": "staged_pipe_uninstalled", "confidence": 0.89, "box": [50, 60, 210, 180] }
    ],
    "exif": {
      "camera": "iPhone 14 Pro",
      "focal_length": "24mm"
    }
  }
}
```

---

## 5. TypeScript Contract Interface

```typescript
export type EvidenceRelationship = 'SUPPORTS' | 'CONTRADICTS' | 'NEUTRAL' | 'INSUFFICIENT';
export type SourceReliability = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNVERIFIED';

export interface LocationPayload {
  latitude?: number;
  longitude?: number;
  address?: string;
  [key: string]: unknown;
}

export interface EvidenceContract {
  evidence_id: string; // UUID
  project_id: string; // UUID
  claim_id?: string | null; // UUID
  source_type: string;
  source_id: string;
  observation: string;
  value?: number | null;
  unit?: string | null;
  timestamp?: string | null; // ISO 8601
  location?: LocationPayload | null;
  confidence: number; // 0.00 - 1.00
  reliability: SourceReliability;
  relationship: EvidenceRelationship;
  metadata: Record<string, unknown>;
  created_at: string; // ISO 8601
}
```
