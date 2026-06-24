from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_hash(*parts: Any) -> str:
    normalized = "|".join("" if part is None else str(part).strip() for part in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def json_hash(payload: Any) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

