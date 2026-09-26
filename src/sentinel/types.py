"""
SENTINEL Types and Data Contracts Specification.
Phase 1A - Investigation Vertical Slice
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


class InvestigationState(str, Enum):
    CREATED = "CREATED"
    INTAKE = "INTAKE"
    CLAIMS_IDENTIFIED = "CLAIMS_IDENTIFIED"
    EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"
    CROSS_CHECK = "CROSS_CHECK"
    CONFLICT_ANALYSIS = "CONFLICT_ANALYSIS"
    DECISION = "DECISION"
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    CORRECTION = "CORRECTION"
    CASE_MEMORY = "CASE_MEMORY"
    CLOSED = "CLOSED"


class EvidenceRelationship(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    NEUTRAL = "NEUTRAL"
    INSUFFICIENT = "INSUFFICIENT"


class SourceReliability(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNVERIFIED = "UNVERIFIED"


class ConflictSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class AgentResult:
    """Agent Output Contract as specified in Phase 1A requirements."""
    agent_type: str
    finding: str
    evidence_ids: List[str]
    confidence: float
    severity: str
    reasoning_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_type": self.agent_type,
            "finding": self.finding,
            "evidence_ids": self.evidence_ids,
            "confidence": self.confidence,
            "severity": self.severity,
            "reasoning_summary": self.reasoning_summary
        }


@dataclass
class Project:
    id: str
    code: str
    name: str
    description: str
    sanctioned_amount: float
    released_amount: float
    currency: str = "INR"
    location_name: Optional[str] = None
    status: str = "ACTIVE"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Claim:
    id: str
    project_id: str
    claim_ref: str
    claimed_by: str
    claim_type: str  # COMPLETION_PERCENTAGE, PHYSICAL_QUANTITY, etc.
    description: str
    claimed_value: float
    unit: str
    claim_date: str
    status: str = "DECLARED"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceItem:
    id: str
    project_id: str
    claim_id: Optional[str]
    source_type: str
    source_id: str
    observation: str
    value: Optional[float]
    unit: Optional[str]
    timestamp: Optional[str]
    location: Optional[Dict[str, Any]]
    confidence: float
    reliability: str
    relationship: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Finding:
    id: str
    investigation_id: str
    project_id: str
    claim_id: Optional[str]
    agent_name: str
    finding_type: str
    summary: str
    reasoning: str
    confidence: float
    evidence_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContradictionRecord:
    id: str
    investigation_id: str
    project_id: str
    claim_id: Optional[str]
    evidence_a_id: str
    evidence_b_id: str
    conflict_description: str
    severity: str
    status: str = "UNRESOLVED"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HumanCorrection:
    id: str
    investigation_id: str
    project_id: str
    claim_id: Optional[str]
    corrected_by: str
    original_interpretation: str
    corrected_interpretation: str
    reason_for_correction: str
    evidence_ids_involved: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CaseMemoryRecord:
    id: str
    human_correction_id: str
    investigation_id: str
    project_id: str
    pattern_type: str
    context_summary: str
    precedent_rule: str
    lessons_learned: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InvestigationEvent:
    id: str
    investigation_id: str
    event_type: str
    state: Optional[str]
    agent_name: Optional[str]
    details: Dict[str, Any]
    timestamp: str
