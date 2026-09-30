"""FastAPI handler captures real 500s via TestClient."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from centralog import CentralogClient
from centralog.frameworks.fastapi import register


def test_fastapi_500_is_captured(monkeypatch):
    import httpx

    sent = {}

    def fake_post(url, *, json=None, headers=None, timeout=None):
        sent["body"] = json
        request = httpx.Request("POST", url, headers=headers)
        return httpx.Response(201, json={}, request=request)

    monkeypatch.setattr(httpx, "post", fake_post)

    client = CentralogClient(
        endpoint="https://centralog.test/api/v1/ingest/events",
        api_key="clk_test_key",
        environment="production",
    )
    app = FastAPI()
    register(app, client)

    @app.get("/boom")
    def boom():
        raise RuntimeError("kaboom")

    response = TestClient(app, raise_server_exceptions=False).get("/boom")

    assert response.status_code == 500
    assert sent["body"]["exception"]["class"] == "builtins.RuntimeError"
    assert sent["body"]["exception"]["message"] == "kaboom"
    assert sent["body"]["request"]["method"] == "GET"
    assert sent["body"]["request"]["url"].endswith("/boom")
