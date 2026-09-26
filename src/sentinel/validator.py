"""
SENTINEL Output Validator.
Enforces strict JSON schema validation, severity bounds, and evidence grounding checks.
Rejects hallucinated evidence IDs.
"""
import json
import re
from typing import Set, Dict, Any, Tuple
from sentinel.types import AgentResult


class OutputValidationError(Exception):
    """Raised when model output fails JSON parsing, schema validation, or evidence grounding."""
    pass


def validate_and_normalize_output(
    raw_output: str,
    expected_agent_type: str,
    valid_evidence_ids: Set[str]
) -> Tuple[AgentResult, Dict[str, Any]]:
    """
    Parses and validates raw model output against the Agent Output Contract.
    
    Returns:
        (AgentResult, validation_metadata_dict)
    
    Raises:
        OutputValidationError: If JSON is malformed, missing required keys, or contains invalid severity.
    """
    if not raw_output or not raw_output.strip():
        raise OutputValidationError("Raw model output is empty.")

    # 1. Clean Markdown JSON Code Fences if present
    cleaned = raw_output.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned).strip()

    # 2. Parse JSON
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise OutputValidationError(f"Malformed JSON in model output: {e}") from e

    if not isinstance(data, dict):
        raise OutputValidationError("Model output JSON must be a dictionary object.")

    # 3. Check Required Keys
    required_keys = {"agent_type", "finding", "evidence_ids", "confidence", "severity", "reasoning_summary"}
    missing = required_keys - set(data.keys())
    if missing:
        raise OutputValidationError(f"Missing required keys in model output: {missing}")

    agent_type = str(data["agent_type"]).strip()
    finding = str(data["finding"]).strip()
    raw_ev_ids = data["evidence_ids"]
    confidence = float(data["confidence"])
    severity = str(data["severity"]).strip().upper()
    reasoning_summary = str(data["reasoning_summary"]).strip()

    # 4. Severity Validation
    if severity not in ("LOW", "MEDIUM", "HIGH"):
        raise OutputValidationError(f"Unsupported severity value '{severity}'. Must be LOW, MEDIUM, or HIGH.")

    # 5. Confidence Bound Check
    if not (0.0 <= confidence <= 1.0):
        confidence = max(0.0, min(1.0, confidence))

    # 6. Hallucinated Evidence ID Grounding Check
    if not isinstance(raw_ev_ids, list):
        raise OutputValidationError("Field 'evidence_ids' must be a list of strings.")

    cleaned_ev_ids = []
    hallucinated_ids = []
    for ev_id in raw_ev_ids:
        ev_id_str = str(ev_id).strip()
        if ev_id_str in valid_evidence_ids:
            cleaned_ev_ids.append(ev_id_str)
        else:
            hallucinated_ids.append(ev_id_str)

    if hallucinated_ids:
        raise OutputValidationError(
            f"Hallucinated evidence IDs detected: {hallucinated_ids}. "
            f"Allowed evidence IDs for this invocation: {list(valid_evidence_ids)}"
        )

    # 7. Non-Accusatory Sanity Check (Fraud / Accusation check)
    forbidden_terms = ["fraud", "guilty", "criminal", "scam", "corrupt", "deny payment"]
    for term in forbidden_terms:
        if term in reasoning_summary.lower():
            raise OutputValidationError(f"Model output violates non-accusatory invariant (contains forbidden term '{term}').")

    result = AgentResult(
        agent_type=agent_type,
        finding=finding,
        evidence_ids=cleaned_ev_ids,
        confidence=confidence,
        severity=severity,
        reasoning_summary=reasoning_summary
    )

    validation_metadata = {
        "status": "VALIDATED",
        "hallucinated_ids_count": len(hallucinated_ids),
        "input_evidence_count": len(valid_evidence_ids),
        "validated_evidence_count": len(cleaned_ev_ids)
    }

    return result, validation_metadata
