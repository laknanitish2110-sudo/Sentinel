"""
SENTINEL Database Layer.
Provides relational persistence and strict foreign key / security boundary checks.
"""
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sentinel.types import (
    Project, Claim, EvidenceItem, Finding, ContradictionRecord,
    HumanCorrection, CaseMemoryRecord, InvestigationEvent, InvestigationState
)


class UnauthorizedWriteError(Exception):
    """Raised when an unauthorized user attempts an auditor-only database write."""
    pass


class SentinelDB:
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._init_schema()

    def _init_schema(self):
        with self.conn:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    sanctioned_amount REAL NOT NULL,
                    released_amount REAL NOT NULL DEFAULT 0.0,
                    currency TEXT NOT NULL DEFAULT 'INR',
                    location_name TEXT,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS claims (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    claim_ref TEXT,
                    claimed_by TEXT NOT NULL,
                    claim_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    claimed_value REAL,
                    unit TEXT,
                    claim_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'DECLARED',
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    claim_id TEXT REFERENCES claims(id) ON DELETE SET NULL,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    observation TEXT NOT NULL,
                    value REAL,
                    unit TEXT,
                    timestamp TEXT,
                    location TEXT,
                    confidence REAL NOT NULL DEFAULT 1.0,
                    reliability TEXT NOT NULL DEFAULT 'MEDIUM',
                    relationship TEXT NOT NULL DEFAULT 'NEUTRAL',
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS investigations (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    current_state TEXT NOT NULL DEFAULT 'CREATED',
                    previous_state TEXT,
                    orchestrator_notes TEXT,
                    initiated_by TEXT NOT NULL DEFAULT 'SYSTEM',
                    completed_at TEXT,
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    investigation_id TEXT NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    claim_id TEXT REFERENCES claims(id) ON DELETE SET NULL,
                    agent_name TEXT NOT NULL,
                    finding_type TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    reasoning TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 1.0,
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS findings_evidence (
                    finding_id TEXT NOT NULL REFERENCES findings(id) ON DELETE CASCADE,
                    evidence_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
                    PRIMARY KEY (finding_id, evidence_id)
                );

                CREATE TABLE IF NOT EXISTS contradictions (
                    id TEXT PRIMARY KEY,
                    investigation_id TEXT NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    claim_id TEXT REFERENCES claims(id) ON DELETE SET NULL,
                    evidence_a_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
                    evidence_b_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
                    conflict_description TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'MEDIUM',
                    status TEXT NOT NULL DEFAULT 'UNRESOLVED',
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS human_corrections (
                    id TEXT PRIMARY KEY,
                    investigation_id TEXT NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    claim_id TEXT REFERENCES claims(id) ON DELETE SET NULL,
                    corrected_by TEXT NOT NULL,
                    original_interpretation TEXT NOT NULL,
                    corrected_interpretation TEXT NOT NULL,
                    reason_for_correction TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS human_corrections_evidence (
                    human_correction_id TEXT NOT NULL REFERENCES human_corrections(id) ON DELETE CASCADE,
                    evidence_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
                    PRIMARY KEY (human_correction_id, evidence_id)
                );

                CREATE TABLE IF NOT EXISTS case_memory (
                    id TEXT PRIMARY KEY,
                    human_correction_id TEXT NOT NULL REFERENCES human_corrections(id) ON DELETE CASCADE,
                    investigation_id TEXT NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    pattern_type TEXT NOT NULL,
                    context_summary TEXT NOT NULL,
                    precedent_rule TEXT NOT NULL,
                    lessons_learned TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS investigation_events (
                    id TEXT PRIMARY KEY,
                    investigation_id TEXT NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
                    event_type TEXT NOT NULL,
                    state TEXT,
                    agent_name TEXT,
                    details TEXT NOT NULL DEFAULT '{}',
                    timestamp TEXT NOT NULL
                );
            """)

    # -------------------------------------------------------------------------
    # RLS Security Simulation: Auditor Role Enforcement
    # -------------------------------------------------------------------------
    def _verify_auditor_role(self, user_role: str):
        if user_role not in ("auditor", "service_role"):
            raise UnauthorizedWriteError(
                f"Unauthorized write attempt by role '{user_role}'. Auditor or service_role credentials required."
            )

    # -------------------------------------------------------------------------
    # Data Ingestion Methods
    # -------------------------------------------------------------------------
    def save_project(self, project: Project):
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO projects (id, code, name, description, sanctioned_amount, released_amount, currency, location_name, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (project.id, project.code, project.name, project.description, project.sanctioned_amount,
                  project.released_amount, project.currency, project.location_name, project.status, json.dumps(project.metadata)))

    def save_claim(self, claim: Claim):
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO claims (id, project_id, claim_ref, claimed_by, claim_type, description, claimed_value, unit, claim_date, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (claim.id, claim.project_id, claim.claim_ref, claim.claimed_by, claim.claim_type, claim.description,
                  claim.claimed_value, claim.unit, claim.claim_date, claim.status, json.dumps(claim.metadata)))

    def save_evidence(self, evidence: EvidenceItem):
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO evidence (id, project_id, claim_id, source_type, source_id, observation, value, unit, timestamp, location, confidence, reliability, relationship, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (evidence.id, evidence.project_id, evidence.claim_id, evidence.source_type, evidence.source_id,
                  evidence.observation, evidence.value, evidence.unit, evidence.timestamp,
                  json.dumps(evidence.location) if evidence.location else None, evidence.confidence,
                  evidence.reliability, evidence.relationship, json.dumps(evidence.metadata)))

    # -------------------------------------------------------------------------
    # Investigation Persistence Methods
    # -------------------------------------------------------------------------
    def create_investigation(self, project_id: str, title: str, user_role: str = "service_role") -> str:
        self._verify_auditor_role(user_role)
        investigation_id = str(uuid.uuid4())
        with self.conn:
            self.conn.execute("""
                INSERT INTO investigations (id, project_id, title, current_state, previous_state, initiated_by)
                VALUES (?, ?, ?, 'CREATED', NULL, 'SYSTEM')
            """, (investigation_id, project_id, title))
        self.record_event(investigation_id, "INVESTIGATION_CREATED", "CREATED", details={"title": title})
        return investigation_id

    def update_investigation_state(self, investigation_id: str, new_state: str, previous_state: str, notes: Optional[str] = None, user_role: str = "service_role"):
        self._verify_auditor_role(user_role)
        with self.conn:
            self.conn.execute("""
                UPDATE investigations
                SET current_state = ?, previous_state = ?, orchestrator_notes = ?
                WHERE id = ?
            """, (new_state, previous_state, notes, investigation_id))
        self.record_event(investigation_id, "STATE_TRANSITION", new_state, details={"previous_state": previous_state, "notes": notes})

    def save_finding(self, finding: Finding, user_role: str = "service_role"):
        self._verify_auditor_role(user_role)
        with self.conn:
            self.conn.execute("""
                INSERT INTO findings (id, investigation_id, project_id, claim_id, agent_name, finding_type, summary, reasoning, confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (finding.id, finding.investigation_id, finding.project_id, finding.claim_id, finding.agent_name,
                  finding.finding_type, finding.summary, finding.reasoning, finding.confidence, json.dumps(finding.metadata)))
            
            # Save junction entries with FK enforcement
            for ev_id in finding.evidence_ids:
                self.conn.execute("""
                    INSERT INTO findings_evidence (finding_id, evidence_id) VALUES (?, ?)
                """, (finding.id, ev_id))

    def save_contradiction(self, contradiction: ContradictionRecord, user_role: str = "service_role"):
        self._verify_auditor_role(user_role)
        # Foreign Key check: ensure evidence_a_id and evidence_b_id exist
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM evidence WHERE id IN (?, ?)", (contradiction.evidence_a_id, contradiction.evidence_b_id))
        found_ids = {row["id"] for row in cur.fetchall()}
        if contradiction.evidence_a_id not in found_ids or contradiction.evidence_b_id not in found_ids:
            raise ValueError(f"Invalid evidence reference in contradiction: {contradiction.evidence_a_id}, {contradiction.evidence_b_id}")

        with self.conn:
            self.conn.execute("""
                INSERT INTO contradictions (id, investigation_id, project_id, claim_id, evidence_a_id, evidence_b_id, conflict_description, severity, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (contradiction.id, contradiction.investigation_id, contradiction.project_id, contradiction.claim_id,
                  contradiction.evidence_a_id, contradiction.evidence_b_id, contradiction.conflict_description,
                  contradiction.severity, contradiction.status, json.dumps(contradiction.metadata)))

    def save_human_correction(self, correction: HumanCorrection, user_role: str = "auditor"):
        self._verify_auditor_role(user_role)
        with self.conn:
            self.conn.execute("""
                INSERT INTO human_corrections (id, investigation_id, project_id, claim_id, corrected_by, original_interpretation, corrected_interpretation, reason_for_correction, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (correction.id, correction.investigation_id, correction.project_id, correction.claim_id,
                  correction.corrected_by, correction.original_interpretation, correction.corrected_interpretation,
                  correction.reason_for_correction, json.dumps(correction.metadata)))
            
            for ev_id in correction.evidence_ids_involved:
                self.conn.execute("""
                    INSERT INTO human_corrections_evidence (human_correction_id, evidence_id) VALUES (?, ?)
                """, (correction.id, ev_id))

    def save_case_memory(self, memory: CaseMemoryRecord, user_role: str = "service_role"):
        self._verify_auditor_role(user_role)
        with self.conn:
            self.conn.execute("""
                INSERT INTO case_memory (id, human_correction_id, investigation_id, project_id, pattern_type, context_summary, precedent_rule, lessons_learned, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (memory.id, memory.human_correction_id, memory.investigation_id, memory.project_id,
                  memory.pattern_type, memory.context_summary, memory.precedent_rule, memory.lessons_learned, json.dumps(memory.metadata)))

    def record_event(self, investigation_id: str, event_type: str, state: Optional[str] = None, agent_name: Optional[str] = None, details: Dict[str, Any] = None):
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        with self.conn:
            self.conn.execute("""
                INSERT INTO investigation_events (id, investigation_id, event_type, state, agent_name, details, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (event_id, investigation_id, event_type, state, agent_name, json.dumps(details or {}), timestamp))

    # -------------------------------------------------------------------------
    # Retrieval Methods
    # -------------------------------------------------------------------------
    def get_project(self, project_id: str) -> Optional[Project]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cur.fetchone()
        if not row: return None
        return Project(id=row["id"], code=row["code"], name=row["name"], description=row["description"],
                       sanctioned_amount=row["sanctioned_amount"], released_amount=row["released_amount"],
                       currency=row["currency"], location_name=row["location_name"], status=row["status"],
                       metadata=json.loads(row["metadata"]))

    def get_claims_for_project(self, project_id: str) -> List[Claim]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM claims WHERE project_id = ?", (project_id,))
        return [Claim(id=row["id"], project_id=row["project_id"], claim_ref=row["claim_ref"],
                      claimed_by=row["claimed_by"], claim_type=row["claim_type"], description=row["description"],
                      claimed_value=row["claimed_value"], unit=row["unit"], claim_date=row["claim_date"],
                      status=row["status"], metadata=json.loads(row["metadata"])) for row in cur.fetchall()]

    def get_evidence_for_project(self, project_id: str) -> List[EvidenceItem]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM evidence WHERE project_id = ?", (project_id,))
        return [EvidenceItem(id=row["id"], project_id=row["project_id"], claim_id=row["claim_id"],
                             source_type=row["source_type"], source_id=row["source_id"], observation=row["observation"],
                             value=row["value"], unit=row["unit"], timestamp=row["timestamp"],
                             location=json.loads(row["location"]) if row["location"] else None,
                             confidence=row["confidence"], reliability=row["reliability"], relationship=row["relationship"],
                             metadata=json.loads(row["metadata"])) for row in cur.fetchall()]

    def get_case_memories_for_pattern(self, pattern_type: str) -> List[CaseMemoryRecord]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM case_memory WHERE pattern_type = ?", (pattern_type,))
        return [CaseMemoryRecord(id=row["id"], human_correction_id=row["human_correction_id"],
                                 investigation_id=row["investigation_id"], project_id=row["project_id"],
                                 pattern_type=row["pattern_type"], context_summary=row["context_summary"],
                                 precedent_rule=row["precedent_rule"], lessons_learned=row["lessons_learned"],
                                 metadata=json.loads(row["metadata"])) for row in cur.fetchall()]

    def get_investigation_events(self, investigation_id: str) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM investigation_events WHERE investigation_id = ? ORDER BY timestamp ASC", (investigation_id,))
        return [{"id": row["id"], "event_type": row["event_type"], "state": row["state"],
                 "agent_name": row["agent_name"], "details": json.loads(row["details"]), "timestamp": row["timestamp"]} for row in cur.fetchall()]

    def close(self):
        self.conn.close()
