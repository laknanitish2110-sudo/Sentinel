"""
Sentinel Agentic Investigation Loop.
An autonomous agent that plans, executes tools, checks results, re-plans on failure,
and delivers a grounded conclusion — modeled on the plan-code-test-replan pattern.
"""
import uuid
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

from sentinel.db import SentinelDB
from sentinel.types import (
    Project, Claim, EvidenceItem, ContradictionRecord,
    InvestigationState, CaseMemoryRecord, AgentResult
)

try:
    from PIL import Image, ImageFilter, ImageStat
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@dataclass
class ToolCall:
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    timestamp: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class AgentStep:
    step_type: str  # "plan", "tool_call", "check", "replan", "deliver"
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def to_dict(self):
        return asdict(self)


# --- Tool definitions for Claude tool-use ---

AGENT_TOOLS = [
    {
        "name": "analyze_photo",
        "description": "Analyze a construction site photograph using computer vision. Extracts dimensions, edge density (activity indicator), dominant colors, brightness, and estimates visible infrastructure length.",
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Path to the site photo"},
                "target_object": {"type": "string", "description": "What to look for: pipe, trench, machinery, etc."}
            },
            "required": ["image_path"]
        }
    },
    {
        "name": "cross_check_values",
        "description": "Compare two evidence items to check if their reported values are consistent. Flags discrepancies greater than 10%.",
        "input_schema": {
            "type": "object",
            "properties": {
                "evidence_a_id": {"type": "string", "description": "ID of first evidence item"},
                "evidence_b_id": {"type": "string", "description": "ID of second evidence item"},
                "metric": {"type": "string", "description": "What metric to compare: length, amount, completion_pct"}
            },
            "required": ["evidence_a_id", "evidence_b_id"]
        }
    },
    {
        "name": "verify_financial_trail",
        "description": "Trace the money flow: sanctioned budget → released tranches → contractor claims → invoices. Flags gaps where claimed work exceeds released funds.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project to verify"}
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "search_precedents",
        "description": "Search case memory for historical precedents matching a discrepancy pattern. Returns past auditor corrections and lessons learned.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern_type": {"type": "string", "description": "Pattern to search: STAGED_MATERIAL_DISCREPANCY, PARTIAL_PAYMENT_TIMING, etc."}
            },
            "required": ["pattern_type"]
        }
    },
    {
        "name": "flag_discrepancy",
        "description": "Record a discrepancy found between two evidence items. Creates a formal contradiction record with severity assessment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "evidence_a_id": {"type": "string", "description": "First evidence ID"},
                "evidence_b_id": {"type": "string", "description": "Second evidence ID"},
                "description": {"type": "string", "description": "What the discrepancy is"},
                "severity": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]}
            },
            "required": ["evidence_a_id", "evidence_b_id", "description", "severity"]
        }
    },
    {
        "name": "request_human_review",
        "description": "Escalate to a human auditor when the agent cannot resolve a discrepancy autonomously. Provide a clear reason.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Why human review is needed"},
                "unresolved_items": {"type": "array", "items": {"type": "string"}, "description": "Evidence IDs that need human judgment"}
            },
            "required": ["reason"]
        }
    }
]


class InvestigationAgent:
    """
    Autonomous investigation agent using Claude tool-use in an iterative loop.
    Plan → Execute → Check → Re-plan → Deliver.
    """

    MAX_ITERATIONS = 4

    def __init__(self, db: SentinelDB):
        self.db = db
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.model = "claude-sonnet-4-20250514"
        self.trace: List[AgentStep] = []
        self.contradictions: List[ContradictionRecord] = []

    def investigate(self, project_id: str, uploaded_image_path: Optional[str] = None) -> Dict[str, Any]:
        """Run the full agentic investigation loop."""
        project = self.db.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        claims = self.db.get_claims_for_project(project_id)
        evidence = self.db.get_evidence_for_project(project_id)
        self.trace = []
        self.contradictions = []

        investigation_id = self.db.create_investigation(
            project_id=project_id,
            title=f"Agentic Investigation: {project.name}",
            user_role="service_role"
        )

        if self.api_key:
            final_state, decision = self._run_agentic_loop(
                investigation_id, project, claims, evidence, uploaded_image_path
            )
        else:
            final_state, decision = self._run_deterministic_loop(
                investigation_id, project, claims, evidence, uploaded_image_path
            )

        self.db.update_investigation_state(
            investigation_id, final_state, InvestigationState.DECISION,
            notes=decision, user_role="service_role"
        )

        return {
            "investigation_id": investigation_id,
            "project_id": project_id,
            "final_state": str(final_state).replace("InvestigationState.", ""),
            "decision_summary": decision,
            "trace": [s.to_dict() for s in self.trace],
            "contradiction_count": len(self.contradictions),
            "iterations": len([s for s in self.trace if s.step_type == "check"])
        }

    def _run_agentic_loop(
        self, investigation_id: str, project: Project,
        claims: List[Claim], evidence: List[EvidenceItem],
        uploaded_image_path: Optional[str]
    ) -> tuple:
        """Real agentic loop using Claude tool-use API."""

        # Step 1: PLAN
        system_prompt = self._build_system_prompt(project, claims, evidence, uploaded_image_path)
        messages = [{"role": "user", "content": self._build_initial_prompt(project, claims, evidence, uploaded_image_path)}]

        self._log_step("plan", "Agent analyzing project context and planning investigation",
                       {"project": project.name, "claims": len(claims), "evidence": len(evidence)})

        evidence_map = {e.id: e for e in evidence}
        final_state = InvestigationState.HUMAN_REVIEW_REQUIRED
        decision = ""

        for iteration in range(self.MAX_ITERATIONS):
            response = self._call_claude_with_tools(system_prompt, messages)

            if not response:
                self._log_step("check", "Claude API unavailable, falling back to deterministic analysis", {})
                return self._run_deterministic_loop(investigation_id, project, claims, evidence, uploaded_image_path)

            # Process response blocks
            assistant_content = response.get("content", [])
            messages.append({"role": "assistant", "content": assistant_content})

            tool_uses = [b for b in assistant_content if b.get("type") == "tool_use"]
            text_blocks = [b for b in assistant_content if b.get("type") == "text"]

            if not tool_uses:
                # Agent is done — extract conclusion from text
                conclusion = " ".join(b.get("text", "") for b in text_blocks)
                self._log_step("deliver", "Agent reached conclusion", {"conclusion": conclusion[:300]})

                if "SUPPORTED" in conclusion.upper() and "PARTIALLY" not in conclusion.upper() and "NOT" not in conclusion.upper():
                    final_state = InvestigationState.SUPPORTED
                elif "CONTRADICTED" in conclusion.upper():
                    final_state = InvestigationState.CONTRADICTED
                elif "INSUFFICIENT" in conclusion.upper():
                    final_state = InvestigationState.INSUFFICIENT_EVIDENCE
                elif "PARTIALLY" in conclusion.upper():
                    final_state = InvestigationState.PARTIALLY_SUPPORTED
                else:
                    final_state = InvestigationState.HUMAN_REVIEW_REQUIRED

                decision = conclusion[:500]
                break

            # Execute each tool call
            tool_results = []
            for tool_use in tool_uses:
                tool_name = tool_use["name"]
                tool_input = tool_use.get("input", {})
                tool_id = tool_use["id"]

                self._log_step("tool_call", f"Calling tool: {tool_name}", {"tool": tool_name, "input": tool_input})

                result = self._execute_tool(
                    tool_name, tool_input, investigation_id,
                    project, evidence_map
                )

                self._log_step("tool_call", f"Tool result: {tool_name}",
                               {"tool": tool_name, "result": result})

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": json.dumps(result)
                })

            messages.append({"role": "user", "content": tool_results})

            # Log check step
            self._log_step("check", f"Iteration {iteration + 1} complete, {len(tool_uses)} tools executed",
                           {"iteration": iteration + 1, "tools_used": len(tool_uses)})

        return final_state, decision

    def _run_deterministic_loop(
        self, investigation_id: str, project: Project,
        claims: List[Claim], evidence: List[EvidenceItem],
        uploaded_image_path: Optional[str]
    ) -> tuple:
        """Deterministic fallback that still follows the plan-execute-check pattern."""

        # PLAN
        self._log_step("plan", "Planning investigation (deterministic mode)",
                       {"project": project.name, "claims": len(claims), "evidence": len(evidence),
                        "mode": "deterministic"})

        # EXECUTE: Analyze photo if provided
        if uploaded_image_path:
            photo_result = self._tool_analyze_photo(uploaded_image_path, "infrastructure")
            self._log_step("tool_call", "Analyzing uploaded site photo",
                           {"tool": "analyze_photo", "result": photo_result})

        # EXECUTE: Cross-check evidence values
        mb_items = [e for e in evidence if e.source_type == "MB_RECORD"]
        inspection_items = [e for e in evidence if e.source_type in ("PHYSICAL_INSPECTION", "GEO_PHOTO")]

        for mb in mb_items:
            for insp in inspection_items:
                if mb.value and insp.value and mb.value > 0:
                    cross = self._tool_cross_check(mb, insp)
                    self._log_step("tool_call", f"Cross-checking {mb.source_type} vs {insp.source_type}",
                                   {"tool": "cross_check_values", "result": cross})

                    if cross.get("discrepancy_pct", 0) > 10:
                        disc = self._tool_flag_discrepancy(
                            investigation_id, project.id,
                            mb.id, insp.id,
                            f"Measurement variance: {mb.source_type} reports {mb.value}{mb.unit} "
                            f"but {insp.source_type} shows {insp.value}{insp.unit} "
                            f"({cross['discrepancy_pct']:.1f}% gap)",
                            "HIGH" if cross["discrepancy_pct"] > 30 else "MEDIUM"
                        )
                        self._log_step("tool_call", "Flagging measurement discrepancy",
                                       {"tool": "flag_discrepancy", "result": disc})

        # EXECUTE: Verify financial trail
        financial = self._tool_verify_financial(project, claims, evidence)
        self._log_step("tool_call", "Verifying financial trail",
                       {"tool": "verify_financial_trail", "result": financial})

        # EXECUTE: Search precedents
        precedents = self._tool_search_precedents("STAGED_MATERIAL_DISCREPANCY")
        self._log_step("tool_call", "Searching case memory for precedents",
                       {"tool": "search_precedents", "result": precedents})

        # CHECK
        has_contradictions = len(self.contradictions) > 0
        has_precedent = precedents.get("count", 0) > 0
        has_insufficient = any(e.relationship == "INSUFFICIENT" for e in evidence)

        self._log_step("check", "Evaluating evidence sufficiency",
                       {"contradictions": len(self.contradictions),
                        "precedents_found": precedents.get("count", 0),
                        "has_insufficient": has_insufficient})

        # DECIDE
        if has_contradictions and has_precedent:
            final_state = InvestigationState.PARTIALLY_SUPPORTED
            decision = (f"Evidence partially supports claims. {len(self.contradictions)} discrepancy(ies) found "
                       f"between official records and physical inspection. Historical precedent suggests "
                       f"underground/backfilled work may account for the gap. Human review recommended to confirm.")
        elif has_contradictions:
            final_state = InvestigationState.HUMAN_REVIEW_REQUIRED
            decision = (f"Unresolved discrepancy detected. {len(self.contradictions)} contradiction(s) found. "
                       f"Agent cannot autonomously resolve — escalating to human auditor.")
            self._log_step("tool_call", "Requesting human review",
                           {"tool": "request_human_review",
                            "result": {"reason": decision, "unresolved": len(self.contradictions)}})
        elif has_insufficient:
            final_state = InvestigationState.INSUFFICIENT_EVIDENCE
            decision = "Insufficient evidence to verify claims. Additional documentation required."
        elif all(e.relationship == "SUPPORTS" for e in evidence if e.relationship != "NEUTRAL"):
            final_state = InvestigationState.SUPPORTED
            decision = "All evidence supports the contractor's claims. No discrepancies found."
        else:
            final_state = InvestigationState.PARTIALLY_SUPPORTED
            decision = "Evidence partially supports claims. Some items could not be independently verified."

        self._log_step("deliver", f"Investigation complete: {str(final_state).replace('InvestigationState.', '')}",
                       {"final_state": str(final_state).replace("InvestigationState.", ""),
                        "decision": decision})

        return final_state, decision

    # --- Tool implementations ---

    def _execute_tool(self, tool_name: str, tool_input: Dict, investigation_id: str,
                      project: Project, evidence_map: Dict[str, EvidenceItem]) -> Dict:
        if tool_name == "analyze_photo":
            return self._tool_analyze_photo(tool_input.get("image_path", ""), tool_input.get("target_object", ""))

        elif tool_name == "cross_check_values":
            a = evidence_map.get(tool_input.get("evidence_a_id"))
            b = evidence_map.get(tool_input.get("evidence_b_id"))
            if not a or not b:
                return {"error": "Evidence ID not found", "available_ids": list(evidence_map.keys())}
            return self._tool_cross_check(a, b)

        elif tool_name == "verify_financial_trail":
            claims = self.db.get_claims_for_project(project.id)
            evidence = list(evidence_map.values())
            return self._tool_verify_financial(project, claims, evidence)

        elif tool_name == "search_precedents":
            return self._tool_search_precedents(tool_input.get("pattern_type", ""))

        elif tool_name == "flag_discrepancy":
            return self._tool_flag_discrepancy(
                investigation_id, project.id,
                tool_input.get("evidence_a_id", ""),
                tool_input.get("evidence_b_id", ""),
                tool_input.get("description", ""),
                tool_input.get("severity", "MEDIUM")
            )

        elif tool_name == "request_human_review":
            return {"status": "ESCALATED", "reason": tool_input.get("reason", "")}

        return {"error": f"Unknown tool: {tool_name}"}

    def _tool_analyze_photo(self, image_path: str, target: str = "") -> Dict:
        if PIL_AVAILABLE and image_path and os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                w, h = img.size
                gray = img.convert("L")
                stat = ImageStat.Stat(gray)
                brightness = stat.mean[0]
                edges = gray.filter(ImageFilter.FIND_EDGES)
                edge_stat = ImageStat.Stat(edges)
                edge_density = round(edge_stat.mean[0] / 255.0, 4)
                rgb = img.convert("RGB")
                rgb_stat = ImageStat.Stat(rgb)
                r, g, b = rgb_stat.mean[:3]

                activity_level = "high" if edge_density > 0.15 else "moderate" if edge_density > 0.08 else "low"

                return {
                    "analyzed": True,
                    "dimensions": f"{w}x{h}",
                    "edge_density": edge_density,
                    "activity_level": activity_level,
                    "brightness": round(brightness, 1),
                    "dominant_colors": {"r": round(r, 1), "g": round(g, 1), "b": round(b, 1)},
                    "observation": f"Site photo analysis: {activity_level} construction activity detected. "
                                   f"Edge density {edge_density:.3f} suggests {'active work zone' if edge_density > 0.12 else 'limited visible activity'}."
                }
            except Exception as e:
                return {"analyzed": False, "error": str(e)}

        return {
            "analyzed": False,
            "observation": "No image available for analysis. Using document-based evidence only.",
            "note": "In production, YOLO11 object detection would identify specific infrastructure elements."
        }

    def _tool_cross_check(self, a: EvidenceItem, b: EvidenceItem) -> Dict:
        val_a = a.value or 0
        val_b = b.value or 0
        max_val = max(abs(val_a), abs(val_b), 1)
        discrepancy_pct = round(abs(val_a - val_b) / max_val * 100, 1)

        consistent = discrepancy_pct <= 10
        return {
            "evidence_a": {"id": a.id, "type": a.source_type, "value": val_a, "unit": a.unit},
            "evidence_b": {"id": b.id, "type": b.source_type, "value": val_b, "unit": b.unit},
            "discrepancy_pct": discrepancy_pct,
            "consistent": consistent,
            "assessment": f"Values are {'consistent' if consistent else 'INCONSISTENT'}: "
                         f"{a.source_type} reports {val_a}{a.unit}, "
                         f"{b.source_type} reports {val_b}{b.unit} "
                         f"({discrepancy_pct}% {'gap' if not consistent else 'variance'})."
        }

    def _tool_verify_financial(self, project: Project, claims: List[Claim], evidence: List[EvidenceItem]) -> Dict:
        released_ratio = round(project.released_amount / max(project.sanctioned_amount, 1) * 100, 1)
        completion_claim = next((c for c in claims if c.claim_type == "COMPLETION_PERCENTAGE"), None)
        claimed_pct = completion_claim.claimed_value if completion_claim else 0

        invoices = [e for e in evidence if e.source_type == "INVOICE"]
        invoice_total = sum(e.value or 0 for e in invoices)

        bank_items = [e for e in evidence if e.source_type == "BANK_STATEMENT"]
        has_bank_clearance = any("clear" in (e.observation or "").lower() for e in bank_items)

        fund_gap = claimed_pct - released_ratio

        return {
            "sanctioned": project.sanctioned_amount,
            "released": project.released_amount,
            "released_pct": released_ratio,
            "claimed_completion_pct": claimed_pct,
            "invoice_total": invoice_total,
            "fund_utilization_gap": round(fund_gap, 1),
            "bank_clearance_verified": has_bank_clearance,
            "assessment": f"Contractor claims {claimed_pct}% completion but only {released_ratio}% of budget released. "
                         f"{'Bank clearance verified.' if has_bank_clearance else 'Bank clearance NOT verified — gap in financial trail.'}"
        }

    def _tool_search_precedents(self, pattern_type: str) -> Dict:
        memories = self.db.get_case_memories_for_pattern(pattern_type)
        if not memories:
            return {"count": 0, "precedents": [], "assessment": f"No historical precedents found for pattern '{pattern_type}'."}

        precs = []
        for m in memories:
            precs.append({
                "pattern": m.pattern_type,
                "rule": m.precedent_rule,
                "lesson": m.lessons_learned
            })

        return {
            "count": len(memories),
            "precedents": precs,
            "assessment": f"Found {len(memories)} precedent(s) for '{pattern_type}'. "
                         f"Key lesson: {memories[0].lessons_learned[:200]}"
        }

    def _tool_flag_discrepancy(self, investigation_id: str, project_id: str,
                                ev_a_id: str, ev_b_id: str, description: str, severity: str) -> Dict:
        contradiction = ContradictionRecord(
            id=f"con_{uuid.uuid4().hex[:8]}",
            investigation_id=investigation_id,
            project_id=project_id,
            claim_id=None,
            evidence_a_id=ev_a_id,
            evidence_b_id=ev_b_id,
            conflict_description=description,
            severity=severity,
            status="UNRESOLVED"
        )
        self.contradictions.append(contradiction)
        self.db.save_contradiction(contradiction, user_role="service_role")

        return {
            "recorded": True,
            "contradiction_id": contradiction.id,
            "severity": severity,
            "description": description
        }

    # --- Claude API with tool use ---

    def _call_claude_with_tools(self, system: str, messages: List[Dict]) -> Optional[Dict]:
        if not self.api_key:
            return None

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2024-10-22",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "temperature": 0.0,
            "system": system,
            "tools": AGENT_TOOLS,
            "messages": messages
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

    # --- Prompt construction ---

    def _build_system_prompt(self, project: Project, claims: List[Claim],
                             evidence: List[EvidenceItem], image_path: Optional[str]) -> str:
        return (
            "You are Sentinel, an autonomous AI investigation agent for public infrastructure projects. "
            "Your job is to verify whether a contractor's claims about project completion are supported by evidence.\n\n"
            "INVESTIGATION PROTOCOL:\n"
            "1. PLAN: Analyze available evidence and identify what needs verification\n"
            "2. EXECUTE: Use your tools to cross-check values, analyze photos, verify financial trails\n"
            "3. CHECK: Evaluate if you have enough evidence to reach a conclusion\n"
            "4. If gaps remain, use more tools to investigate further\n"
            "5. DELIVER: State your conclusion clearly\n\n"
            "RULES:\n"
            "- Every claim must be traced to empirical evidence\n"
            "- Never accuse anyone of fraud — report discrepancies factually\n"
            "- When evidence conflicts and you cannot resolve it, request human review\n"
            "- Check for historical precedents before escalating\n"
            "- Use the exact evidence IDs provided — do not fabricate IDs\n\n"
            "When you are done investigating, respond with a text conclusion that includes "
            "the word SUPPORTED, PARTIALLY_SUPPORTED, CONTRADICTED, INSUFFICIENT, or HUMAN_REVIEW_REQUIRED."
        )

    def _build_initial_prompt(self, project: Project, claims: List[Claim],
                              evidence: List[EvidenceItem], image_path: Optional[str]) -> str:
        lines = [f"## Investigation: {project.name}\n"]
        lines.append(f"Budget: {project.currency} {project.sanctioned_amount:,.0f}")
        lines.append(f"Released: {project.currency} {project.released_amount:,.0f}")
        lines.append(f"Location: {project.location_name}\n")

        lines.append("## Claims to verify:")
        for c in claims:
            lines.append(f"- [{c.id}] {c.description} (claimed: {c.claimed_value} {c.unit} by {c.claimed_by})")

        lines.append("\n## Available evidence:")
        for e in evidence:
            lines.append(f"- [{e.id}] {e.source_type} ({e.reliability}): {e.observation[:150]}")
            if e.value:
                lines.append(f"  Value: {e.value} {e.unit} | Relationship: {e.relationship}")

        if image_path:
            lines.append(f"\n## Uploaded site photo: {image_path}")
            lines.append("Use analyze_photo to examine this image.")

        lines.append("\nInvestigate this project now. Start by planning your approach, then use tools to verify the claims.")
        return "\n".join(lines)

    def _log_step(self, step_type: str, description: str, data: Dict[str, Any]):
        self.trace.append(AgentStep(
            step_type=step_type,
            description=description,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat()
        ))
