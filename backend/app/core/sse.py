from __future__ import annotations
import json
from typing import Any, Dict, Optional

def sse_data(obj: Dict[str, Any], event: Optional[str] = None) -> str:
    # Basic SSE framing. Each event ends with a blank line.
    # `event:` is optional; `data:` lines contain JSON.
    payload = json.dumps(obj, ensure_ascii=False)
    if event:
        return f"event: {event}\ndata: {payload}\n\n"
    return f"data: {payload}\n\n"
