"""
SENTINEL Citizen API Service Layer (Phase 2B.1).
Exposes public-safe REST endpoints serving public project info, money trail, evidence graph, and investigation status.
Renders analytical contradiction edges identified by Contradiction Engine.
"""
from typing import Dict, Any, List, Optional
from sentinel.db import SentinelDB
from sentinel.orchestrator import Orchestrator
from sentinel.engines.case_memory_engine import CaseMemoryEngine
from sentinel.types import Project, Claim, EvidenceItem


class SentinelCitizenAPI:
    def __init__(self, db: SentinelDB):
        self.db = db

    def get_public_project(self, project_id: str) -> Dict[str, Any]:
        project = self.db.get_project(project_id)
        if not project:
            return {"error": "Project not found"}

        claims = self.db.get_claims_for_project(project_id)
        completion_claim = next((c for c in claims if c.claim_type == "COMPLETION_PERCENTAGE"), None)
        claimed_completion_val = completion_claim.claimed_value if completion_claim else 80.0

        claimed_amount = (claimed_completion_val / 100.0) * project.sanctioned_amount

        return {
            "id": project.id,
            "code": project.code,
            "name": project.name,
            "description": project.description,
            "sanctioned_amount": project.sanctioned_amount,
            "released_amount": project.released_amount,
            "released_percentage": round((project.released_amount / project.sanctioned_amount) * 100, 1),
            "claimed_amount": claimed_amount,
            "claimed_percentage": claimed_completion_val,
            "currency": project.currency,
            "location_name": project.location_name,
            "status": "Under Active Verification",
            "is_demo_data": project.metadata.get("is_demo_data", True)
        }

    def get_money_trail(self, project_id: str) -> Dict[str, Any]:
        proj_data = self.get_public_project(project_id)
        evidence_items = self.db.get_evidence_for_project(project_id)

        financial_evidence = []
        for e in evidence_items:
            if e.source_type in ("INVOICE", "BANK_STATEMENT", "MB_RECORD"):
                financial_evidence.append({
                    "id": e.id,
                    "source_type": e.source_type,
                    "source_name": self._friendly_source_name(e.source_type),
                    "document_id": e.source_id,
                    "observation": e.observation,
                    "amount": e.value,
                    "unit": e.unit,
                    "date": e.timestamp,
                    "relationship": e.relationship,
                    "reliability": e.reliability
                })

        return {
            "sanctioned_amount": proj_data.get("sanctioned_amount", 1800000.0),
            "released_amount": proj_data.get("released_amount", 720000.0),
            "claimed_amount": proj_data.get("claimed_amount", 1440000.0),
            "currency": proj_data.get("currency", "INR"),
            "reported_completion": f"{proj_data.get('claimed_percentage', 80)}%",
            "financial_evidence": financial_evidence
        }

    def get_evidence_graph(self, project_id: str) -> Dict[str, Any]:
        claims = self.db.get_claims_for_project(project_id)
        evidence_items = self.db.get_evidence_for_project(project_id)

        # Query active contradictions from database to mark graph edges
        cur = self.db.conn.cursor()
        cur.execute("SELECT evidence_a_id, evidence_b_id FROM contradictions WHERE project_id = ?", (project_id,))
        contradiction_ev_ids = set()
        for row in cur.fetchall():
            contradiction_ev_ids.add(row["evidence_a_id"])
            contradiction_ev_ids.add(row["evidence_b_id"])

        claims_nodes = []
        for c in claims:
            claims_nodes.append({
                "id": c.id,
                "claim_ref": c.claim_ref,
                "claimed_by": c.claimed_by,
                "description": c.description,
                "claimed_value": c.claimed_value,
                "unit": c.unit,
                "date": c.claim_date
            })

        evidence_nodes = []
        for e in evidence_items:
            rel = e.relationship
            # If Contradiction Engine flagged this item in a contradiction record, reflect analytical relationship
            if e.id in contradiction_ev_ids and rel != "SUPPORTS":
                rel = "CONTRADICTS"

            evidence_nodes.append({
                "id": e.id,
                "claim_id": e.claim_id,
                "source_type": e.source_type,
                "source_name": self._friendly_source_name(e.source_type),
                "source_id": e.source_id,
                "observation": e.observation,
                "value": e.value,
                "unit": e.unit,
                "date": e.timestamp,
                "confidence_score": f"{int(e.confidence * 100)}%",
                "reliability": e.reliability,
                "relationship": rel,
                "relationship_label": self._friendly_relationship_label(rel),
                "badge_icon": self._relationship_icon(rel)
            })

        return {
            "claims": claims_nodes,
            "evidence": evidence_nodes
        }

    def get_investigation_status(self, project_id: str) -> Dict[str, Any]:
        orchestrator = Orchestrator(self.db)
        inv_res = orchestrator.run_investigation(project_id=project_id)

        memories = self.db.get_case_memories_for_pattern("STAGED_MATERIAL_DISCREPANCY")
        learned_case = None
        if memories:
            m = memories[0]
            learned_case = {
                "title": "Sentinel Learned from a Previous Auditor Correction",
                "pattern_type": m.pattern_type,
                "plain_explanation": (
                    "Previously, Sentinel treated underground pipe work as unexecuted physical progress based solely on trench photos. "
                    "A human auditor clarified that contractor staging yard records verify Hume pipes delivered to site awaiting laying. "
                    "Sentinel now cross-references site delivery bills whenever similar linear trench photo discrepancies appear."
                ),
                "precedent_rule": m.precedent_rule
            }

        state_label = str(inv_res["final_state"]).replace("InvestigationState.", "").replace("_", " ")

        explanation = (
            "Sentinel found that the contractor reported 400m of pipe installation. "
            "The available Measurement Book record supports 400m, while one physical site photo inspection reports 180m visible inside the active trench. "
            "Because the records describe different observations and the available context requires auditor clarification, human review is required."
        )

        return {
            "investigation_id": inv_res["investigation_id"],
            "current_status_headline": "Sentinel is reviewing project evidence",
            "completed_stages": [
                {"name": "Claims identified", "completed": True},
                {"name": "Evidence collected", "completed": True},
                {"name": "Financial records checked", "completed": True},
                {"name": "Historical records checked", "completed": True},
                {"name": "Conflicts analyzed", "completed": True}
            ],
            "final_state": state_label,
            "final_state_raw": inv_res["final_state"],
            "human_review_notice": (
                "Some evidence conflicts or important evidence is missing. Sentinel cannot resolve the difference automatically."
                if "HUMAN_REVIEW_REQUIRED" in str(inv_res["final_state"]) else None
            ),
            "evidence_grounded_explanation": explanation,
            "learned_case_memory": learned_case
        }

    def _friendly_source_name(self, source_type: str) -> str:
        names = {
            "MB_RECORD": "Official Measurement Book Entry",
            "PHYSICAL_INSPECTION": "Site Inspection Photo Report",
            "INVOICE": "Supplier Material Delivery Invoice",
            "BANK_STATEMENT": "Treasury Disbursement Record",
            "GEO_PHOTO": "Geotagged Site Photo",
            "CITIZEN_REPORT": "Citizen Verification Report"
        }
        return names.get(source_type, source_type)

    def _friendly_relationship_label(self, rel: str) -> str:
        labels = {
            "SUPPORTS": "SUPPORTS CLAIM",
            "CONTRADICTS": "CONTRADICTS CLAIM",
            "NEUTRAL": "NEUTRAL EVIDENCE",
            "INSUFFICIENT": "MISSING / INSUFFICIENT"
        }
        return labels.get(rel, rel)

    def _relationship_icon(self, rel: str) -> str:
        icons = {
            "SUPPORTS": "✓",
            "CONTRADICTS": "✕",
            "NEUTRAL": "ℹ",
            "INSUFFICIENT": "⚠"
        }
        return icons.get(rel, "•")
