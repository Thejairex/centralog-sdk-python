"""Fault-tolerant HTTP client for the Centralog ingest API."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from .payload import build_payload

logger = logging.getLogger("centralog")


class CentralogClient:
    """Send error copies to Centralog. Never raises."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        environment: str | None = None,
        release: str | None = None,
        timeout: float = 2.0,
        enabled: bool = True,
    ) -> None:
        self.endpoint = endpoint or os.getenv("CENTRALOG_ENDPOINT", "")
        self.api_key = api_key or os.getenv("CENTRALOG_API_KEY", "")
        self.environment = environment or os.getenv("CENTRALOG_ENVIRONMENT", "production")
        self.release = release if release is not None else os.getenv("CENTRALOG_RELEASE")
        self.timeout = timeout
        if (env_timeout := os.getenv("CENTRALOG_TIMEOUT")) and timeout == 2.0:
            try:
                self.timeout = float(env_timeout)
            except ValueError:
                pass
        self.enabled = enabled and os.getenv("CENTRALOG_ENABLED", "true").lower() not in (
            "0",
            "false",
            "no",
            "off",
        )
        self._extra_context: dict[str, Any] = {}

    def context(self, context: dict[str, Any]) -> None:
        """Merge extra context into every captured event."""
        self._extra_context.update(context)

    def get_context(self) -> dict[str, Any]:
        return dict(self._extra_context)

    def flush_context(self) -> None:
        self._extra_context = {}

    def capture(
        self,
        exception: BaseException,
        context: dict[str, Any] | None = None,
        level: str = "error",
        request: dict[str, Any] | None = None,
        user: dict[str, Any] | None = None,
    ) -> bool:
        """Capture an exception and send a copy to Centralog.

        Returns True on success. Never raises: any failure is logged
        locally at debug level and swallowed.
        """
        if not self.enabled or not self.endpoint or not self.api_key:
            return False

        try:
            merged = {**self._extra_context, **(context or {})}
            payload = build_payload(
                exception,
                environment=self.environment,
                release=self.release,
                level=level,
                context=merged,
                request=request,
                user=user,
            )
            response = httpx.post(
                self.endpoint,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
            return 200 <= response.status_code < 300
        except Exception as exc:  # noqa: BLE001 — reporting must never break the app
            logger.debug("Centralog reporting failed: %s", exc)
            return False
