import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Literal, Self

import anyio

from aioadaptive.limiter import AbstractLimiter, VegasLimiter

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveClientConfig:
    """Configuration for the AdaptiveClient."""

    algorithm: Literal["vegas"] = "vegas"


class AdaptiveClient:
    """Adaptive client that uses a configurable algorithm to adjust the concurrency limit of the session.

    The client will use the session to make requests and will adjust the concurrency limit based on the algorithm.
    The client will retry the request if it fails.
    The client will return the response from the session.
    The client will release the session when the context manager is exited.

    """

    _capacity_limiter: anyio.CapacityLimiter
    _throughput_limiter: AbstractLimiter
    _config: AdaptiveClientConfig

    def __init__(self: Self, config: AdaptiveClientConfig | None = None) -> None:
        """Configure the AdaptiveClient instance.

        Args:
            config (AdaptiveClientConfig | None, optional): Config to use for this instance of adaptive client. Defaults
            to AdaptiveClientConfig().

        """
        self._config = config or AdaptiveClientConfig()
        if self._config.algorithm == "vegas":
            self._throughput_limiter = VegasLimiter()
        else:
            msg = f"Algorithm '{self._config.algorithm}' not supported"
            raise ValueError(msg)
        self._capacity_limiter = anyio.CapacityLimiter(self._throughput_limiter.limit)

    @asynccontextmanager
    async def use(self: Self) -> AsyncGenerator[Self, None]:
        """Context manager for watching the limiter state and adjusting the concurrency limit.

        Yields:
            AsyncGenerator[Self, None]: The client instance.

        """
        async with self._capacity_limiter:
            start = time.time()
            yield self
            end = time.time()
            elapsed = end - start
            new_limit = self._throughput_limiter.update(elapsed)
            self._capacity_limiter.total_tokens = new_limit
