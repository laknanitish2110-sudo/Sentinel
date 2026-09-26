-- =============================================================================
-- SENTINEL SEED DATA (MIGRATION SEED 001 - REVISED FOR PHASE 1A)
-- Description: Realistic Demo Drainage Project Seed Data
-- System: Supabase PostgreSQL
-- =============================================================================

-- Clean up any existing demo records to ensure rerunnable seed execution
DELETE FROM projects WHERE code = 'DEMO-WARD7-DRAIN-2026';

-- -----------------------------------------------------------------------------
-- 1. DEMO PROJECT: Ward 7 Drainage Improvement
-- -----------------------------------------------------------------------------
INSERT INTO projects (
    id,
    code,
    name,
    description,
    sanctioned_amount,
    released_amount,
    currency,
    location_name,
    location_coordinates,
    status,
    metadata
) VALUES (
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'DEMO-WARD7-DRAIN-2026',
    'Ward 7 Drainage Improvement [DEMO DATA]',
    'Construction of RCC storm water drain and laying of 400m main drainage line along Ward 7 primary arterial road. [DEMO DATA - NOT REAL GOVERNMENT DATA]',
    1800000.00, -- Sanctioned: ₹18,00,000
    720000.00,  -- Released: ₹7,20,000 (40%)
    'INR',
    'Ward 7 Arterial Corridor, Zone 3',
    '{"latitude": 12.9716, "longitude": 77.5946, "ward_number": 7}'::jsonb,
    'UNDER_AUDIT',
    '{"is_demo_data": true, "department": "Public Works Department", "contractor": "Apex Infra Works Ltd"}'::jsonb
);

-- -----------------------------------------------------------------------------
-- 2. CONTRACTOR CLAIMS
-- -----------------------------------------------------------------------------
-- Claim A: Contractor claims 80% completion milestone
INSERT INTO claims (
    id,
    project_id,
    claim_ref,
    claimed_by,
    claim_type,
    description,
    claimed_value,
    unit,
    claim_date,
    status,
    metadata
) VALUES (
    'c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22',
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'CLAIM-WARD7-RA-02',
    'Apex Infra Works Ltd',
    'COMPLETION_PERCENTAGE',
    'Contractor submission for 2nd Running Account (RA) Bill claiming 80% physical completion of drainage works.',
    80.00,
    'percent',
    '2026-09-15 10:00:00+00',
    'UNDER_VERIFICATION',
    '{"bill_number": "RA-BILL-002", "is_demo_data": true}'::jsonb
);

-- Claim B: Contractor claims 400m pipe installation
INSERT INTO claims (
    id,
    project_id,
    claim_ref,
    claimed_by,
    claim_type,
    description,
    claimed_value,
    unit,
    claim_date,
    status,
    metadata
) VALUES (
    'c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33',
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'CLAIM-WARD7-PIPE-400M',
    'Apex Infra Works Ltd',
    'PHYSICAL_QUANTITY',
    'Contractor report asserting full installation of 400 meters of 600mm RCC hume pipes along Ward 7 main stretch.',
    400.00,
    'meters',
    '2026-09-15 10:30:00+00',
    'UNDER_VERIFICATION',
    '{"specification": "600mm Class NP3 RCC Hume Pipes", "is_demo_data": true}'::jsonb
);

-- -----------------------------------------------------------------------------
-- 3. EVIDENCE ITEMS
-- -----------------------------------------------------------------------------

-- Evidence 1: Measurement Book (MB) Entry (SUPPORTED evidence)
INSERT INTO evidence (
    id,
    project_id,
    claim_id,
    source_type,
    source_id,
    observation,
    value,
    unit,
    timestamp,
    location,
    confidence,
    reliability,
    relationship,
    metadata
) VALUES (
    'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a44',
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33',
    'MB_RECORD',
    'MB-BOOK-402/PAGE-18',
    'Junior Engineer Measurement Book entry certifying 400m of pipe excavation and laying completed.',
    400.00,
    'meters',
    '2026-09-14 16:00:00+00',
    '{"location_text": "Ward 7 Main Stretch Ch. 0+000 to 0+400"}'::jsonb,
    0.95,
    'HIGH',
    'SUPPORTS',
    '{"signatory": "Junior Engineer Ward 7", "document_type": "Government Measurement Book"}'::jsonb
);

-- Evidence 2: Ground Physical Inspection Report & Photo (CONTRADICTORY evidence)
INSERT INTO evidence (
    id,
    project_id,
    claim_id,
    source_type,
    source_id,
    observation,
    value,
    unit,
    timestamp,
    location,
    confidence,
    reliability,
    relationship,
    metadata
) VALUES (
    'e2eebc99-9c0b-4ef8-bb6d-6bb9bd380a55',
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33',
    'PHYSICAL_INSPECTION',
    'INSP-2026-W7-009',
    'Independent site audit photo inspection verified only 180 meters of pipe laid directly inside the active trench.',
    180.00,
    'meters',
    '2026-09-18 09:15:00+00',
    '{"latitude": 12.9720, "longitude": 77.5950, "address": "Ward 7 Trench Section B"}'::jsonb,
    0.90,
    'HIGH',
    'CONTRADICTS',
    '{"inspector": "Third Party Engineering Auditor", "photo_url": "storage://audit-photos/ward7_trench_180m.jpg"}'::jsonb
);

-- Evidence 3: Supplier Invoice for Pipes Purchase (NEUTRAL evidence)
INSERT INTO evidence (
    id,
    project_id,
    claim_id,
    source_type,
    source_id,
    observation,
    value,
    unit,
    timestamp,
    location,
    confidence,
    reliability,
    relationship,
    metadata
) VALUES (
    'e3eebc99-9c0b-4ef8-bb6d-6bb9bd380a66',
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33',
    'INVOICE',
    'INV-SOUTHERN-CONCRETE-9941',
    'Invoice from Southern Concrete Products confirming procurement and delivery of 400m of RCC hume pipes to site.',
    400.00,
    'meters',
    '2026-09-02 11:00:00+00',
    '{"delivery_site": "Ward 7 Contractor Staging Yard"}'::jsonb,
    0.98,
    'HIGH',
    'NEUTRAL',
    '{"vendor": "Southern Concrete Products Ltd", "invoice_amount": 480000.00, "note": "Proves purchase and site delivery, but not in-ground installation."}'::jsonb
);

-- Evidence 4: Bank Tranche Receipt (MISSING / INSUFFICIENT evidence)
INSERT INTO evidence (
    id,
    project_id,
    claim_id,
    source_type,
    source_id,
    observation,
    value,
    unit,
    timestamp,
    location,
    confidence,
    reliability,
    relationship,
    metadata
) VALUES (
    'e4eebc99-9c0b-4ef8-bb6d-6bb9bd380a77',
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'c1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22',
    'BANK_STATEMENT',
    'TREASURY-DISBURSEMENT-MISSING-02',
    'Treasury records confirm Tranche 1 release (₹7,20,000), but official Bank Clearance Certificate for second claimed tranche is unverified/absent.',
    720000.00,
    'INR',
    '2026-08-10 14:00:00+00',
    NULL,
    0.50,
    'UNVERIFIED',
    'INSUFFICIENT',
    '{"missing_fields": ["bank_clearance_ref", "utr_number"], "audit_flag": "EVIDENTIARY_GAP"}'::jsonb
);

-- -----------------------------------------------------------------------------
-- 4. INVESTIGATION SESSION RECORD
-- -----------------------------------------------------------------------------
INSERT INTO investigations (
    id,
    project_id,
    title,
    current_state,
    previous_state,
    orchestrator_notes,
    initiated_by,
    completed_at,
    metadata
) VALUES (
    'i1eebc99-9c0b-4ef8-bb6d-6bb9bd380a88',
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'Investigation into Ward 7 Claim RA-02 Discrepancy',
    'HUMAN_REVIEW_REQUIRED',
    'CONFLICT_ANALYSIS',
    'Orchestrator detected high-severity conflict between MB entry (400m installed) and Physical Photo Inspection (180m installed in trench). Human auditor intervention requested.',
    'Sentinel Orchestrator v0.1',
    NULL,
    '{"conflict_severity": "HIGH", "is_demo_data": true}'::jsonb
);

-- -----------------------------------------------------------------------------
-- 5. AGENT FINDINGS & CONTRADICTIONS
-- -----------------------------------------------------------------------------

-- Finding by Financial Cross-Check Agent
INSERT INTO findings (
    id,
    investigation_id,
    project_id,
    claim_id,
    agent_name,
    finding_type,
    summary,
    reasoning,
    confidence,
    metadata
) VALUES (
    'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380a99',
    'i1eebc99-9c0b-4ef8-bb6d-6bb9bd380a88',
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33',
    'Financial Cross-Check Agent',
    'PHYSICAL_MEASUREMENT_DISCREPANCY',
    'Major physical discrepancy detected between government MB record and third-party site photos.',
    'Measurement Book MB-402 asserts 400m pipe installed. Third-party physical inspection photo confirms only 180m in trench. Invoice INV-9941 confirms 400m purchased and delivered to site yard.',
    0.92,
    '{"discrepancy_meters": 220.00}'::jsonb
);

-- Junction Links for Finding <-> Evidence
INSERT INTO findings_evidence (finding_id, evidence_id) VALUES
('f1eebc99-9c0b-4ef8-bb6d-6bb9bd380a99', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a44'),
('f1eebc99-9c0b-4ef8-bb6d-6bb9bd380a99', 'e2eebc99-9c0b-4ef8-bb6d-6bb9bd380a55'),
('f1eebc99-9c0b-4ef8-bb6d-6bb9bd380a99', 'e3eebc99-9c0b-4ef8-bb6d-6bb9bd380a66');

-- Contradiction Record
INSERT INTO contradictions (
    id,
    investigation_id,
    project_id,
    claim_id,
    evidence_a_id,
    evidence_b_id,
    conflict_description,
    severity,
    status,
    metadata
) VALUES (
    'x1eebc99-9c0b-4ef8-bb6d-6bb9bd380ab1',
    'i1eebc99-9c0b-4ef8-bb6d-6bb9bd380a88',
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33',
    'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', -- MB entry (400m)
    'e2eebc99-9c0b-4ef8-bb6d-6bb9bd380a55', -- Physical Inspection (180m)
    'Direct physical conflict: Measurement Book certifies 400m installed in trench, while site inspection photo proves only 180m laid in trench.',
    'HIGH',
    'UNRESOLVED',
    '{"variance_percent": 55.00}'::jsonb
);

-- -----------------------------------------------------------------------------
-- 6. HUMAN CORRECTION RECORD
-- -----------------------------------------------------------------------------
INSERT INTO human_corrections (
    id,
    investigation_id,
    project_id,
    claim_id,
    corrected_by,
    original_interpretation,
    corrected_interpretation,
    reason_for_correction,
    metadata
) VALUES (
    'h1eebc99-9c0b-4ef8-bb6d-6bb9bd380ac2',
    'i1eebc99-9c0b-4ef8-bb6d-6bb9bd380a88',
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33',
    'Chief Municipal Auditor K. Sharma',
    'System flagged 220m of pipe as unexecuted work / missing physical progress based solely on trench photo.',
    'Site inspection verified 180m laid in trench, PLUS 220m of Hume pipes stacked adjacent to trench in staging yard ready for laying. Work is in active progress.',
    'The site inspector photo captured only the active trench line (180m) but omitted the adjacent contractor staging yard where remaining 220m of Hume pipes were stacked on site. MB entry reflected material-at-site + installed progress combined.',
    '{"action_taken": "Updated claim status to PARTIALLY_SUPPORTED", "is_demo_data": true}'::jsonb
);

-- Junction Links for Human Correction <-> Evidence
INSERT INTO human_corrections_evidence (human_correction_id, evidence_id) VALUES
('h1eebc99-9c0b-4ef8-bb6d-6bb9bd380ac2', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a44'),
('h1eebc99-9c0b-4ef8-bb6d-6bb9bd380ac2', 'e2eebc99-9c0b-4ef8-bb6d-6bb9bd380a55'),
('h1eebc99-9c0b-4ef8-bb6d-6bb9bd380ac2', 'e3eebc99-9c0b-4ef8-bb6d-6bb9bd380a66');

-- -----------------------------------------------------------------------------
-- 7. CASE MEMORY RECORD
-- -----------------------------------------------------------------------------
INSERT INTO case_memory (
    id,
    human_correction_id,
    investigation_id,
    project_id,
    pattern_type,
    context_summary,
    precedent_rule,
    lessons_learned,
    metadata
) VALUES (
    'm1eebc99-9c0b-4ef8-bb6d-6bb9bd380ad3',
    'h1eebc99-9c0b-4ef8-bb6d-6bb9bd380ac2',
    'i1eebc99-9c0b-4ef8-bb6d-6bb9bd380a88',
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'STAGED_MATERIAL_DISCREPANCY',
    'Discrepancy between Measurement Book quantity and site trench photos in pipe laying projects.',
    'When evaluating linear pipe installation claims against trench photos, agents must check whether supplier invoices confirm 100% material delivery to site yard. If material is confirmed on site, flag variance as STAGED_MATERIAL_IN_PROGRESS rather than UNEXECUTED_WORK.',
    'Trench photos frequently capture only active excavation cuts. Always cross-examine material purchase bills and staging yard photos before flagging high-severity installation failure.',
    '{"applicable_tags": ["drainage", "pipe_laying", "material_on_site"], "is_demo_data": true}'::jsonb
);
