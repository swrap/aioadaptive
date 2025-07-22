import logging
import sys
from typing import Self

from aioadaptive.limiter._limiter import AbstractLimiter

ALPHA = 2
BETA = 4
LIMIT_DEFAULT = 10

logger = logging.getLogger(__name__)


class VegasLimiter(AbstractLimiter):
    _limit: int
    _limit_max: int
    _min_round_trip_time: float | None = None
    _alpha: float
    _beta: float

    def __init__(
        self: Self,
        limit: int = LIMIT_DEFAULT,
        limit_max: int = sys.maxsize,
        alpha: float = ALPHA,
        beta: float = BETA,
    ) -> None:
        self._limit = limit
        self._limit_max = limit_max
        self._alpha = alpha
        self._beta = beta

    def update(self: Self, round_trip_time: float) -> int:
        if self._min_round_trip_time is None:
            self._min_round_trip_time = round_trip_time
            return self._limit

        self._min_round_trip_time = min(self._min_round_trip_time, round_trip_time)
        queue_size = self._limit * (1 - (self._min_round_trip_time / round_trip_time))

        if queue_size < self._alpha:
            self._limit = min(self._limit + 1, self._limit_max)
        elif queue_size > self._beta:
            self._limit = max(1, self._limit - 1)

        # https://github.com/Netflix/concurrency-limits/blob/main/concurrency-limits-core/src/main/java/com/netflix/concurrency/limits/limit/VegasLimit.java#L39-L40
        self._alpha = max(ALPHA, self._limit * 0.1)
        self._beta = max(BETA, self._limit * 0.2)

        debug_msg = (
            f"RTT: {round_trip_time}ms, Queue Size: {queue_size}, "
            f"Limit: {self._limit}, Queue Low: {self._alpha}, Queue High: {self._beta}"
        )
        logger.debug(debug_msg)

        # TODO: Future work is to update estimator: https://github.com/Netflix/concurrency-limits/blob/main/concurrency-limits-core/src/main/java/com/netflix/concurrency/limits/limit/VegasLimit.java#L279-L321

        return self._limit

    @property
    def limit(self: Self) -> int:
        return self._limit
