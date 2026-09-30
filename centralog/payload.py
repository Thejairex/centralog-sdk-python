"""Build ingest payloads matching the Centralog Fase 8 contract."""

from __future__ import annotations

import traceback
import uuid
from typing import Any


def build_payload(
    exception: BaseException,
    environment: str,
    release: str | None = None,
    level: str = "error",
    context: dict[str, Any] | None = None,
    request: dict[str, Any] | None = None,
    user: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an ingest payload from an exception and optional context.

    Mirrors the Laravel SDK PayloadBuilder output exactly.
    """
    tb = exception.__traceback__
    # Walk to the deepest user frame for file/line, like Laravel reports throw site.
    deepest: dict[str, Any] = {"file": "<unknown>", "line": 0}
    if tb is not None:
        frames = traceback.extract_tb(tb)
        if frames:
            last = frames[-1]
            deepest = {"file": last.filename, "line": last.lineno or 0}

    return {
        "event_id": str(uuid.uuid4()),
        "environment": environment,
        "release": release,
        "level": level,
        "exception": {
            "class": f"{type(exception).__module__}.{type(exception).__name__}",
            "message": str(exception) or type(exception).__name__,
            "file": deepest["file"],
            "line": deepest["line"],
            "trace": "".join(traceback.format_exception(exception)),
        },
        "request": request,
        "user": user,
        "context": context if context else None,
    }
