"""Flask integration: register an error handler that reports 500s."""

from __future__ import annotations

try:
    from flask import Flask, Response, request
    from werkzeug.exceptions import HTTPException
except ImportError:  # pragma: no cover
    Flask = None  # type: ignore[assignment]
    Response = None  # type: ignore[assignment]
    request = None  # type: ignore[assignment]
    HTTPException = Exception  # type: ignore[assignment,misc]

from ..client import CentralogClient


def register(app: Flask, client: CentralogClient | None = None) -> CentralogClient:
    """Register Centralog error reporting on a Flask app.

    Captures unhandled 500s. Your error responses stay unchanged.
    """
    client = client or CentralogClient()

    @app.errorhandler(Exception)
    def _report(error: BaseException):  # type: ignore[no-untyped-def]
        if isinstance(error, HTTPException) and getattr(error, "code", 500) < 500:
            raise error
        client.capture(
            error,
            request={
                "method": request.method,
                "url": request.url,
                "route": request.url_rule.endpoint if request.url_rule else None,
            },
        )
        return Response("Internal Server Error", status=500)

    return client
