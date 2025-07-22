"""Adaptive client for sending API calls.

This package provides a client for sending API calls with adaptive concurrency.
"""

from aioadaptive.client import AdaptiveClient, AdaptiveClientConfig

__all__ = ["AdaptiveClient", "AdaptiveClientConfig"]
