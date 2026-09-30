"""Django integration: middleware that reports unhandled exceptions."""

from __future__ import annotations

import logging

from ..client import CentralogClient

logger = logging.getLogger("centralog")


class CentralogMiddleware:
    """Report unhandled exceptions, then re-raise so Django handles them.

    Add to MIDDLEWARE. Never swallows: the exception always propagates.
    """

    def __init__(self, get_response):  # type: ignore[no-untyped-def]
        self.get_response = get_response
        self.client = CentralogClient()

    def __call__(self, request):  # type: ignore[no-untyped-def]
        return self.get_response(request)

    def process_exception(self, request, exception) -> None:  # type: ignore[no-untyped-def]
        try:
            resolver_match = getattr(request, "resolver_match", None)
            self.client.capture(
                exception,
                request={
                    "method": request.method,
                    "url": request.build_absolute_uri(),
                    "route": getattr(resolver_match, "view_name", None),
                },
            )
        except Exception as exc:  # noqa: BLE001 — reporting must never break the app
            logger.debug("Centralog Django middleware failed: %s", exc)
