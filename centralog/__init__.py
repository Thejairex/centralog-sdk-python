"""Centralog Python SDK — error copies for your Centralog platform."""

from .client import CentralogClient
from .payload import build_payload

__all__ = ["CentralogClient", "build_payload"]
__version__ = "0.1.0"
