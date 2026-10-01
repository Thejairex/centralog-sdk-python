"""Flask error handler captures 500s."""

import httpx
from flask import Flask

from centralog import CentralogClient
from centralog.frameworks.flask import register


def _fake_ok(monkeypatch):
    sent = {}

    def fake_post(url, *, json=None, headers=None, timeout=None):
        sent["body"] = json
        request = httpx.Request("POST", url, headers=headers)
        return httpx.Response(201, json={}, request=request)

    monkeypatch.setattr(httpx, "post", fake_post)
    return sent


def test_flask_500_is_captured(monkeypatch):
    sent = _fake_ok(monkeypatch)

    client = CentralogClient(
        endpoint="https://centralog.test/api/v1/ingest/events",
        api_key="clk_test_key",
        environment="production",
    )
    app = Flask(__name__)
    register(app, client)

    @app.get("/boom")
    def boom():
        raise RuntimeError("kaboom")

    response = app.test_client().get("/boom")

    assert response.status_code == 500
    assert sent["body"]["exception"]["class"] == "builtins.RuntimeError"
    assert sent["body"]["exception"]["message"] == "kaboom"
    assert sent["body"]["request"]["method"] == "GET"
    assert sent["body"]["request"]["url"].endswith("/boom")


def test_flask_404_is_not_captured(monkeypatch):
    sent = _fake_ok(monkeypatch)

    client = CentralogClient(
        endpoint="https://centralog.test/api/v1/ingest/events",
        api_key="clk_test_key",
        environment="production",
    )
    app = Flask(__name__)
    register(app, client)

    response = app.test_client().get("/missing")

    assert response.status_code == 404
    assert sent.get("body") is None
