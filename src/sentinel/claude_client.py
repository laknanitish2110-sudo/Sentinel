"""
SENTINEL Claude Client & Execution Wrapper.
Handles API invocations to Anthropic Claude API, mock injection for testing, graceful error fallback, and audit logging.
"""
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Set, Dict, Any, Optional, Callable, Tuple
from sentinel.types import AgentResult
from sentinel.validator import validate_and_normalize_output, OutputValidationError


class ClaudeClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.mock_provider: Optional[Callable[[str], str]] = None

    def set_mock_provider(self, provider: Optional[Callable[[str], str]]):
        """Allows test suite to inject deterministic mock responses without live API calls."""
        self.mock_provider = provider

    def invoke_agent_reasoning(
        self,
        investigation_id: str,
        agent_type: str,
        prompt_version: str,
        prompt_text: str,
        valid_evidence_ids: Set[str],
        fallback_result: AgentResult,
        db=None
    ) -> Tuple[AgentResult, Dict[str, Any]]:
        """
        Invokes Claude API (or mock provider) and validates output against Evidence Grounding rules.
        Returns (AgentResult, invocation_audit_metadata).
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        invocation_metadata = {
            "investigation_id": investigation_id,
            "agent_type": agent_type,
            "prompt_version": prompt_version,
            "model_identifier": self.model,
            "timestamp": timestamp,
            "input_evidence_ids": list(valid_evidence_ids),
            "success": False,
            "validation_status": "PENDING",
            "error_details": None
        }

        # 1. Use Mock Provider if set (for Unit Tests)
        if self.mock_provider is not None:
            try:
                raw_response = self.mock_provider(prompt_text)
                result, val_meta = validate_and_normalize_output(raw_response, agent_type, valid_evidence_ids)
                invocation_metadata["success"] = True
                invocation_metadata["validation_status"] = val_meta["status"]
                if db:
                    db.record_event(investigation_id, "MODEL_INVOCATION_SUCCESS", agent_name=agent_type, details=invocation_metadata)
                return result, invocation_metadata
            except OutputValidationError as e:
                invocation_metadata["success"] = False
                invocation_metadata["validation_status"] = "VALIDATION_FAILED"
                invocation_metadata["error_details"] = str(e)
                if db:
                    db.record_event(investigation_id, "MODEL_VALIDATION_FAILURE", agent_name=agent_type, details=invocation_metadata)
                return fallback_result, invocation_metadata

        # 2. Live API Call if Key is Present
        if not self.api_key:
            invocation_metadata["error_details"] = "ANTHROPIC_API_KEY environment variable missing."
            invocation_metadata["validation_status"] = "FALLBACK_USED"
            if db:
                db.record_event(investigation_id, "MODEL_UNAVAILABLE_FALLBACK", agent_name=agent_type, details=invocation_metadata)
            return fallback_result, invocation_metadata

        try:
            raw_response = self._call_anthropic_api(prompt_text)
            result, val_meta = validate_and_normalize_output(raw_response, agent_type, valid_evidence_ids)
            invocation_metadata["success"] = True
            invocation_metadata["validation_status"] = val_meta["status"]
            if db:
                db.record_event(investigation_id, "MODEL_INVOCATION_SUCCESS", agent_name=agent_type, details=invocation_metadata)
            return result, invocation_metadata

        except (urllib.error.URLError, Exception, OutputValidationError) as e:
            invocation_metadata["success"] = False
            invocation_metadata["validation_status"] = "MODEL_ERROR_FALLBACK"
            invocation_metadata["error_details"] = str(e)
            if db:
                db.record_event(investigation_id, "MODEL_INVOCATION_ERROR", agent_name=agent_type, details=invocation_metadata)
            return fallback_result, invocation_metadata

    def _call_anthropic_api(self, prompt_text: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "temperature": 0.0,
            "messages": [
                {"role": "user", "content": prompt_text}
            ]
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=30) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            # Extract text from Anthropic response structure
            content_blocks = res_json.get("content", [])
            if content_blocks and "text" in content_blocks[0]:
                return content_blocks[0]["text"]
            raise ValueError("Unexpected response structure from Anthropic API.")
