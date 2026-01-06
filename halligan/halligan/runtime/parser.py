from __future__ import annotations

import json
import re
from typing import Any

from halligan.runtime.errors import ParseError

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


def parse_json_from_response(text: str) -> Any:
    """
    Parse a JSON object from a model response.

    The model may return:
    - raw JSON
    - JSON wrapped in a fenced code block
    - extra explanation text around the JSON
    """
    if text is None:
        raise ParseError("Empty response (None)")

    raw = text.strip()
    if not raw:
        raise ParseError("Empty response")

    # 1) Direct JSON
    try:
        return json.loads(raw)
    except Exception:
        pass

    # 2) ```json ... ```
    fence_match = _JSON_FENCE_RE.search(raw)
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception as exc:
            raise ParseError(f"Failed to parse fenced JSON: {exc}") from exc

    # 3) Best-effort: first '{' to last '}'
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = raw[start : end + 1]
        try:
            return json.loads(candidate)
        except Exception as exc:
            raise ParseError(f"Failed to parse extracted JSON: {exc}") from exc

    raise ParseError("No JSON object found in response")
