"""Payload structure matches the Centralog Fase 8 ingest contract."""


def test_payload_matches_contract_structure():
    from centralog import build_payload

    try:
        raise RuntimeError("Payment failed")
    except RuntimeError as exc:
        payload = build_payload(exc, "production", release="2026.09.30.1")

    assert set(payload) == {
        "event_id",
        "environment",
        "release",
        "level",
        "exception",
        "request",
        "user",
        "context",
    }
    assert payload["environment"] == "production"
    assert payload["release"] == "2026.09.30.1"
    assert payload["level"] == "error"
    assert payload["exception"]["class"] == "builtins.RuntimeError"
    assert payload["exception"]["message"] == "Payment failed"
    assert payload["exception"]["file"].endswith("test_payload.py")
    assert isinstance(payload["exception"]["line"], int)
    assert isinstance(payload["exception"]["trace"], str)


def test_payload_event_id_unique_per_build():
    from centralog import build_payload

    try:
        raise RuntimeError("x")
    except RuntimeError as exc:
        first = build_payload(exc, "production")
        second = build_payload(exc, "production")

    assert first["event_id"] != second["event_id"]


def test_payload_custom_level_and_context():
    from centralog import build_payload

    try:
        raise RuntimeError("Slow query")
    except RuntimeError as exc:
        payload = build_payload(exc, "staging", level="warning", context={"query_ms": 4200})

    assert payload["level"] == "warning"
    assert payload["context"] == {"query_ms": 4200}


def test_payload_empty_context_is_null():
    from centralog import build_payload

    try:
        raise RuntimeError("x")
    except RuntimeError as exc:
        payload = build_payload(exc, "production")

    assert payload["context"] is None


def test_payload_exception_without_traceback():
    from centralog import build_payload

    payload = build_payload(RuntimeError("detached"), "production")

    assert payload["exception"]["file"] == "<unknown>"
    assert payload["exception"]["line"] == 0
