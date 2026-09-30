"""FastAPI integration: register an exception handler that reports 500s."""

from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
except ImportError:  # pragma: no cover
    FastAPI = None  # type: ignore[assignment]
    Request = None  # type: ignore[assignment]
    JSONResponse = None  # type: ignore[assignment]

from ..client import CentralogClient


def register(
    app: FastAPI,
    client: CentralogClient | None = None,
    *,
    capture_http_exceptions: bool = False,
) -> CentralogClient:
    """Register Centralog error reporting on a FastAPI app.

    Captures unhandled 500s (and optionally HTTPException) without
    changing the responses your app returns.
    """
    client = client or CentralogClient()

    async def _report(request: Request, exc: BaseException) -> None:
        route = request.scope.get("route")
        client.capture(
            exc,
            request={
                "method": request.method,
                "url": str(request.url),
                "route": getattr(route, "name", None) or getattr(route, "path", None),
            },
        )

    async def _handle_500(request: Request, exc: Exception) -> Any:
        await _report(request, exc)
        return JSONResponse({"detail": "Internal Server Error"}, status_code=500)

    async def _handle_http(request: Request, exc: Any) -> Any:
        from fastapi import HTTPException

        if isinstance(exc, HTTPException) and exc.status_code >= 500:
            await _report(request, exc)
        raise exc

    app.add_exception_handler(Exception, _handle_500)
    if capture_http_exceptions:
        from fastapi import HTTPException

        app.add_exception_handler(HTTPException, _handle_http)

    return client
