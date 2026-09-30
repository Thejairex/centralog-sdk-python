"""Client posts with Bearer auth and never raises."""

import httpx

from centralog import CentralogClient


def _client(**overrides):
    base = {
        "endpoint": "https://centralog.test/api/v1/ingest/events",
        "api_key": "clk_test_key",
        "environment": "production",
        "release": "2026.09.30.1",
        "timeout": 2.0,
        "enabled": True,
    }
    base.update(overrides)
    return CentralogClient(**base)


def _fake_ok(monkeypatch):
    sent = {}

    def fake_post(url, *, json=None, headers=None, timeout=None):
        sent["url"] = url
        sent["auth"] = (headers or {}).get("Authorization")
        sent["body"] = json
        request = httpx.Request("POST", url, headers=headers)
        return httpx.Response(201, json={"event_id": "event_123"}, request=request)

    monkeypatch.setattr(httpx, "post", fake_post)
    return sent


def test_capture_posts_with_bearer_auth(monkeypatch):
    sent = _fake_ok(monkeypatch)

    assert _client().capture(RuntimeError("Payment failed")) is True
    assert sent["url"] == "https://centralog.test/api/v1/ingest/events"
    assert sent["auth"] == "Bearer clk_test_key"
    assert sent["body"]["exception"]["class"] == "builtins.RuntimeError"
    assert sent["body"]["exception"]["message"] == "Payment failed"
    assert sent["body"]["environment"] == "production"
    assert sent["body"]["release"] == "2026.09.30.1"
    assert sent["body"]["event_id"]


def test_capture_false_on_server_error(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *a, **k: httpx.Response(500, request=httpx.Request("POST", "https://x")),
    )

    assert _client().capture(RuntimeError("x")) is False


def test_capture_false_on_connection_failure(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(httpx, "post", boom)

    assert _client().capture(RuntimeError("x")) is False


def test_capture_disabled_sends_nothing(monkeypatch):
    calls = []
    monkeypatch.setattr(httpx, "post", lambda *a, **k: calls.append(1) or httpx.Response(201))

    assert _client(enabled=False).capture(RuntimeError("x")) is False
    assert calls == []


def test_capture_missing_endpoint_or_key_sends_nothing(monkeypatch):
    calls = []
    monkeypatch.setattr(httpx, "post", lambda *a, **k: calls.append(1) or httpx.Response(201))

    assert _client(endpoint="").capture(RuntimeError("x")) is False
    assert _client(api_key="").capture(RuntimeError("x")) is False
    assert calls == []


def test_extra_context_merged(monkeypatch):
    _fake_ok(monkeypatch)
    client = _client()
    client.context({"tenant": "acme"})

    assert client.get_context() == {"tenant": "acme"}
    assert client.capture(RuntimeError("x"), {"order_id": 1}) is True

    client.flush_context()

    assert client.get_context() == {}
