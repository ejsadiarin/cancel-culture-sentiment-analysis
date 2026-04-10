from __future__ import annotations

import random
import time
from dataclasses import dataclass

import instaloader


@dataclass(slots=True)
class SessionConfig:
    min_delay_s: float = 1.4
    max_delay_s: float = 3.2
    max_retries: int = 4


class InstagramSession:
    def __init__(self, config: SessionConfig, loader: instaloader.Instaloader) -> None:
        self.config = config
        self.loader = loader

    def human_delay(self) -> None:
        time.sleep(random.uniform(self.config.min_delay_s, self.config.max_delay_s))

    def with_retry(self, fn):
        last_exc: Exception | None = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                return fn()
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt == self.config.max_retries:
                    break
                self.human_delay()
                time.sleep(min(12, attempt * 2.0 + random.uniform(0.3, 1.3)))
        if last_exc:
            raise last_exc
        raise RuntimeError("Unexpected retry flow")
