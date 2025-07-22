from abc import ABC, abstractmethod
from typing import Self


class AbstractLimiter(ABC):
    @abstractmethod
    def update(self: Self, round_trip_time: float) -> int:
        pass
