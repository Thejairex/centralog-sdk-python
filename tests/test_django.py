"""Django middleware reports exceptions and lets them propagate."""

import httpx

from centralog import CentralogClient
from centralog.frameworks.django import CentralogMiddleware


class _FakeResolverMatch:
    view_name = "orders.charge"


class _FakeRequest:
    method = "POST"
    url = "https://api.example.com/api/payments"

    def build_absolute_uri(self):
        return self.url


def _client_with_fake_http(monkeypatch):
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
    return client, sent


def test_django_process_exception_captures(monkeypatch):
    client, sent = _client_with_fake_http(monkeypatch)
    middleware = CentralogMiddleware(lambda r: "ok")
    middleware.client = client

    request = _FakeRequest()
    request.resolver_match = _FakeResolverMatch()

    exception = RuntimeError("kaboom")

    result = middleware.process_exception(request, exception)

    assert result is None
    assert sent["body"]["exception"]["class"] == "builtins.RuntimeError"
    assert sent["body"]["exception"]["message"] == "kaboom"
    assert sent["body"]["request"]["method"] == "POST"
    assert sent["body"]["request"]["url"] == "https://api.example.com/api/payments"
    assert sent["body"]["request"]["route"] == "orders.charge"


def test_django_process_exception_without_resolver(monkeypatch):
    client, sent = _client_with_fake_http(monkeypatch)
    middleware = CentralogMiddleware(lambda r: "ok")
    middleware.client = client

    request = _FakeRequest()

    middleware.process_exception(request, RuntimeError("boom"))

    assert sent["body"]["request"]["route"] is None


def test_django_middleware_calls_get_response(monkeypatch):
    calls = []

    def get_response(request):
        calls.append(request)
        return "response"

    middleware = CentralogMiddleware(get_response)
    request = _FakeRequest()

    assert middleware(request) == "response"
    assert calls == [request]


def test_django_process_exception_never_raises_on_reporting_failure(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(httpx, "post", boom)

    middleware = CentralogMiddleware(lambda r: "ok")

    # Should not raise even though the HTTP call fails.
    middleware.process_exception(_FakeRequest(), RuntimeError("x"))
    assert True


def test_django_middleware_client_defaults(monkeypatch):
    middleware = CentralogMiddleware(lambda r: "ok")
    assert isinstance(middleware.client, CentralogClient)
