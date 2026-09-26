-- =============================================================================
-- SENTINEL DATABASE SCHEMA (MIGRATION 001 - REVISED FOR PHASE 1A)
-- Description: Core schema for Sentinel Agentic Evidence Intelligence System
-- System: Supabase PostgreSQL
-- Fixes: P1-1 (Junction tables for FK integrity), P1-2 (Auditor role RLS enforcement)
-- =============================================================================

-- Enable pgcrypto extension for UUID generation if not already active
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------------------------
-- 1. PROJECTS TABLE
-- Master record of public infrastructure projects.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    sanctioned_amount NUMERIC(15,2) NOT NULL CHECK (sanctioned_amount > 0),
    released_amount NUMERIC(15,2) NOT NULL DEFAULT 0.00 CHECK (released_amount >= 0),
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    location_name TEXT,
    location_coordinates JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('PLANNING', 'ACTIVE', 'UNDER_AUDIT', 'COMPLETED', 'SUSPENDED')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE projects IS 'Master registry of public work projects subject to evidence verification.';
COMMENT ON COLUMN projects.sanctioned_amount IS 'Total government sanctioned budget allocation in specified currency.';
COMMENT ON COLUMN projects.released_amount IS 'Total funds released/disbursed to contractor/agency to date.';

-- -----------------------------------------------------------------------------
-- 2. CLAIMS TABLE
-- Contractor claims and formal assertions submitted for project progress.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    claim_ref VARCHAR(100),
    claimed_by TEXT NOT NULL,
    claim_type VARCHAR(50) NOT NULL CHECK (claim_type IN ('COMPLETION_PERCENTAGE', 'PHYSICAL_QUANTITY', 'FINANCIAL_REIMBURSEMENT', 'MILESTONE_ACHIEVED')),
    description TEXT NOT NULL,
    claimed_value NUMERIC(15,2),
    unit VARCHAR(50),
    claim_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'DECLARED' CHECK (status IN ('DECLARED', 'UNDER_VERIFICATION', 'SUPPORTED', 'PARTIALLY_SUPPORTED', 'CONTRADICTED', 'INCONCLUSIVE')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE claims IS 'Contractor assertions regarding physical progress, completion percentages, or fund claims.';

-- -----------------------------------------------------------------------------
-- 3. EVIDENCE TABLE
-- Standardized evidence contract storing empirical physical & financial observations.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    claim_id UUID REFERENCES claims(id) ON DELETE SET NULL,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('MB_RECORD', 'INVOICE', 'GEO_PHOTO', 'BANK_STATEMENT', 'PHYSICAL_INSPECTION', 'CITIZEN_REPORT', 'AUDIT_NOTE')),
    source_id VARCHAR(255) NOT NULL,
    observation TEXT NOT NULL,
    value NUMERIC(15,2),
    unit VARCHAR(50),
    timestamp TIMESTAMPTZ,
    location JSONB,
    confidence NUMERIC(3,2) NOT NULL DEFAULT 1.00 CHECK (confidence >= 0.00 AND confidence <= 1.00),
    reliability VARCHAR(20) NOT NULL DEFAULT 'MEDIUM' CHECK (reliability IN ('HIGH', 'MEDIUM', 'LOW', 'UNVERIFIED')),
    relationship VARCHAR(20) NOT NULL DEFAULT 'NEUTRAL' CHECK (relationship IN ('SUPPORTS', 'CONTRADICTS', 'NEUTRAL', 'INSUFFICIENT')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE evidence IS 'Normalized evidence contract records. Stores physical and financial observations, NOT raw LLM conclusions.';

-- -----------------------------------------------------------------------------
-- 4. INVESTIGATIONS TABLE
-- State machine container tracking individual investigation sessions.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS investigations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    current_state VARCHAR(50) NOT NULL DEFAULT 'CREATED' CHECK (current_state IN (
        'CREATED', 'INTAKE', 'CLAIMS_IDENTIFIED', 'EVIDENCE_COLLECTION',
        'CROSS_CHECK', 'CONFLICT_ANALYSIS', 'DECISION', 'SUPPORTED',
        'PARTIALLY_SUPPORTED', 'CONTRADICTED', 'INSUFFICIENT_EVIDENCE',
        'HUMAN_REVIEW_REQUIRED', 'CORRECTION', 'CASE_MEMORY', 'CLOSED'
    )),
    previous_state VARCHAR(50),
    orchestrator_notes TEXT,
    initiated_by TEXT NOT NULL DEFAULT 'SYSTEM',
    completed_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE investigations IS 'Tracks investigation session state machine execution for a project.';

-- -----------------------------------------------------------------------------
-- 5. FINDINGS TABLE
-- Agent reasoning outputs and analytical findings synthesized during cross-checks.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    claim_id UUID REFERENCES claims(id) ON DELETE SET NULL,
    agent_name VARCHAR(50) NOT NULL,
    finding_type VARCHAR(50) NOT NULL,
    summary TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    confidence NUMERIC(3,2) NOT NULL DEFAULT 1.00 CHECK (confidence >= 0.00 AND confidence <= 1.00),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE findings IS 'Agent reasoning findings and synthesized evaluations operating over raw evidence.';

-- Junction Table for Findings <-> Evidence (P1 Fix: Individual FK Integrity)
CREATE TABLE IF NOT EXISTS findings_evidence (
    finding_id UUID NOT NULL REFERENCES findings(id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    PRIMARY KEY (finding_id, evidence_id)
);

COMMENT ON TABLE findings_evidence IS 'Relational junction table mapping individual evidence items to findings with strict FK integrity.';

-- -----------------------------------------------------------------------------
-- 6. CONTRADICTIONS TABLE
-- Explicit conflict hyper-edges connecting pair-wise conflicting evidence items.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contradictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    claim_id UUID REFERENCES claims(id) ON DELETE SET NULL,
    evidence_a_id UUID NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    evidence_b_id UUID NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    conflict_description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'MEDIUM' CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    status VARCHAR(20) NOT NULL DEFAULT 'UNRESOLVED' CHECK (status IN ('UNRESOLVED', 'RESOLVED_BY_HUMAN', 'DISMISSED')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE contradictions IS 'Pairs of evidence items determined to be in mutual conflict during investigation.';

-- -----------------------------------------------------------------------------
-- 7. HUMAN_CORRECTIONS TABLE
-- First-class audit records capturing human expert overrides of system decisions.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS human_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    claim_id UUID REFERENCES claims(id) ON DELETE SET NULL,
    corrected_by TEXT NOT NULL,
    original_interpretation TEXT NOT NULL,
    corrected_interpretation TEXT NOT NULL,
    reason_for_correction TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE human_corrections IS 'Authoritative human auditor corrections that override agent reasoning outputs.';

-- Junction Table for Human Corrections <-> Evidence (P1 Fix: Individual FK Integrity)
CREATE TABLE IF NOT EXISTS human_corrections_evidence (
    human_correction_id UUID NOT NULL REFERENCES human_corrections(id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    PRIMARY KEY (human_correction_id, evidence_id)
);

COMMENT ON TABLE human_corrections_evidence IS 'Relational junction table mapping evidence involved in a human correction with strict FK integrity.';

-- -----------------------------------------------------------------------------
-- 8. CASE_MEMORY TABLE
-- Structured precedent rules generated from human corrections for RAG retrieval.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS case_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    human_correction_id UUID NOT NULL REFERENCES human_corrections(id) ON DELETE CASCADE,
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    pattern_type VARCHAR(50) NOT NULL,
    context_summary TEXT NOT NULL,
    precedent_rule TEXT NOT NULL,
    lessons_learned TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE case_memory IS 'Case memory precedents created from human corrections to inform future agent runs.';

-- -----------------------------------------------------------------------------
-- 9. INVESTIGATION_EVENTS TABLE (Observability Audit Trail)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS investigation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    state VARCHAR(50),
    agent_name VARCHAR(50),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE investigation_events IS 'Audit trail tracking state transitions, agent invocations, and decisions.';

-- =============================================================================
-- INDEXES
-- Optimizing lookup performance across projects, claims, evidence, and state lookup.
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_claims_project_id ON claims(project_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);

CREATE INDEX IF NOT EXISTS idx_evidence_project_id ON evidence(project_id);
CREATE INDEX IF NOT EXISTS idx_evidence_claim_id ON evidence(claim_id);
CREATE INDEX IF NOT EXISTS idx_evidence_source_type ON evidence(source_type);
CREATE INDEX IF NOT EXISTS idx_evidence_relationship ON evidence(relationship);
CREATE INDEX IF NOT EXISTS idx_evidence_timestamp ON evidence(timestamp);

CREATE INDEX IF NOT EXISTS idx_investigations_project_id ON investigations(project_id);
CREATE INDEX IF NOT EXISTS idx_investigations_state ON investigations(current_state);

CREATE INDEX IF NOT EXISTS idx_findings_investigation_id ON findings(investigation_id);
CREATE INDEX IF NOT EXISTS idx_findings_project_id ON findings(project_id);
CREATE INDEX IF NOT EXISTS idx_findings_claim_id ON findings(claim_id);

CREATE INDEX IF NOT EXISTS idx_findings_evidence_finding_id ON findings_evidence(finding_id);
CREATE INDEX IF NOT EXISTS idx_findings_evidence_evidence_id ON findings_evidence(evidence_id);

CREATE INDEX IF NOT EXISTS idx_contradictions_investigation_id ON contradictions(investigation_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_claim_id ON contradictions(claim_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_evidence_a ON contradictions(evidence_a_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_evidence_b ON contradictions(evidence_b_id);

CREATE INDEX IF NOT EXISTS idx_human_corrections_investigation_id ON human_corrections(investigation_id);
CREATE INDEX IF NOT EXISTS idx_human_corrections_project_id ON human_corrections(project_id);

CREATE INDEX IF NOT EXISTS idx_human_corrections_evidence_hc_id ON human_corrections_evidence(human_correction_id);
CREATE INDEX IF NOT EXISTS idx_human_corrections_evidence_ev_id ON human_corrections_evidence(evidence_id);

CREATE INDEX IF NOT EXISTS idx_case_memory_correction_id ON case_memory(human_correction_id);
CREATE INDEX IF NOT EXISTS idx_case_memory_pattern ON case_memory(pattern_type);

CREATE INDEX IF NOT EXISTS idx_investigation_events_investigation ON investigation_events(investigation_id);

-- =============================================================================
-- AUTOMATIC UPDATED_AT TRIGGER
-- Helper function and triggers to update timestamps automatically.
-- =============================================================================

CREATE OR REPLACE FUNCTION set_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION set_updated_at_column();
CREATE OR REPLACE TRIGGER trg_claims_updated_at BEFORE UPDATE ON claims FOR EACH ROW EXECUTE FUNCTION set_updated_at_column();
CREATE OR REPLACE TRIGGER trg_evidence_updated_at BEFORE UPDATE ON evidence FOR EACH ROW EXECUTE FUNCTION set_updated_at_column();
CREATE OR REPLACE TRIGGER trg_investigations_updated_at BEFORE UPDATE ON investigations FOR EACH ROW EXECUTE FUNCTION set_updated_at_column();

-- =============================================================================
-- SECURITY & SUPABASE ROW LEVEL SECURITY (RLS) POLICIES
-- P1 Fix: Tightened RLS write policies ensuring auditor role verification.
-- =============================================================================

-- Enable RLS across all Sentinel tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE investigations ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE contradictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE human_corrections ENABLE ROW LEVEL SECURITY;
ALTER TABLE human_corrections_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE investigation_events ENABLE ROW LEVEL SECURITY;

-- Helper function to check if current JWT user has auditor role
CREATE OR REPLACE FUNCTION is_auditor()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN (auth.jwt() ->> 'role' = 'auditor') OR (current_user = 'service_role');
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Public / Citizen Read Policies (projects, claims, evidence, finished investigation summaries)
CREATE POLICY "Public Read Access for Projects" ON projects FOR SELECT TO public USING (true);
CREATE POLICY "Public Read Access for Claims" ON claims FOR SELECT TO public USING (true);
CREATE POLICY "Public Read Access for Evidence" ON evidence FOR SELECT TO public USING (true);
CREATE POLICY "Public Read Access for Public Investigation Summary" ON investigations
    FOR SELECT TO public USING (current_state IN ('SUPPORTED', 'PARTIALLY_SUPPORTED', 'CONTRADICTED', 'INSUFFICIENT_EVIDENCE', 'CLOSED'));

-- Service Role Full Access Policies
CREATE POLICY "Service Role Full Access Projects" ON projects FOR ALL TO service_role USING (true);
CREATE POLICY "Service Role Full Access Claims" ON claims FOR ALL TO service_role USING (true);
CREATE POLICY "Service Role Full Access Evidence" ON evidence FOR ALL TO service_role USING (true);
CREATE POLICY "Service Role Full Access Investigations" ON investigations FOR ALL TO service_role USING (true);
CREATE POLICY "Service Role Full Access Findings" ON findings FOR ALL TO service_role USING (true);
CREATE POLICY "Service Role Full Access Findings Evidence" ON findings_evidence FOR ALL TO service_role USING (true);
CREATE POLICY "Service Role Full Access Contradictions" ON contradictions FOR ALL TO service_role USING (true);
CREATE POLICY "Service Role Full Access Human Corrections" ON human_corrections FOR ALL TO service_role USING (true);
CREATE POLICY "Service Role Full Access Human Corrections Evidence" ON human_corrections_evidence FOR ALL TO service_role USING (true);
CREATE POLICY "Service Role Full Access Case Memory" ON case_memory FOR ALL TO service_role USING (true);
CREATE POLICY "Service Role Full Access Investigation Events" ON investigation_events FOR ALL TO service_role USING (true);

-- Authenticated User Read Policies (Internal Auditors can read all audit records)
CREATE POLICY "Authenticated Auditors Read Investigations" ON investigations FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated Auditors Read Findings" ON findings FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated Auditors Read Findings Evidence" ON findings_evidence FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated Auditors Read Contradictions" ON contradictions FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated Auditors Read Human Corrections" ON human_corrections FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated Auditors Read Human Corrections Evidence" ON human_corrections_evidence FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated Auditors Read Case Memory" ON case_memory FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated Auditors Read Investigation Events" ON investigation_events FOR SELECT TO authenticated USING (true);

-- P1 Fix: Write Policies Restricted to Verified Auditor Role (Denies ordinary authenticated users)
CREATE POLICY "Auditors Only Insert/Update Investigations" ON investigations
    FOR ALL TO authenticated USING (is_auditor()) WITH CHECK (is_auditor());

CREATE POLICY "Auditors Only Insert/Update Findings" ON findings
    FOR ALL TO authenticated USING (is_auditor()) WITH CHECK (is_auditor());

CREATE POLICY "Auditors Only Insert/Update Findings Evidence" ON findings_evidence
    FOR ALL TO authenticated USING (is_auditor()) WITH CHECK (is_auditor());

CREATE POLICY "Auditors Only Insert/Update Contradictions" ON contradictions
    FOR ALL TO authenticated USING (is_auditor()) WITH CHECK (is_auditor());

CREATE POLICY "Auditors Only Insert/Update Human Corrections" ON human_corrections
    FOR ALL TO authenticated USING (is_auditor()) WITH CHECK (is_auditor());

CREATE POLICY "Auditors Only Insert/Update Human Corrections Evidence" ON human_corrections_evidence
    FOR ALL TO authenticated USING (is_auditor()) WITH CHECK (is_auditor());

CREATE POLICY "Auditors Only Insert/Update Case Memory" ON case_memory
    FOR ALL TO authenticated USING (is_auditor()) WITH CHECK (is_auditor());

CREATE POLICY "Auditors Only Insert Investigation Events" ON investigation_events
    FOR INSERT TO authenticated WITH CHECK (is_auditor());
