from __future__ import annotations

import random
import time
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Callable

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright


@dataclass(slots=True)
class SessionConfig:
    headless: bool = True
    storage_state_path: str | None = None
    timeout_ms: int = 45000
    min_delay_s: float = 0.8
    max_delay_s: float = 2.2


class TikTokSession(AbstractContextManager["TikTokSession"]):
    def __init__(self, config: SessionConfig) -> None:
        self.config = config
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None

    @property
    def context(self) -> BrowserContext:
        if self._context is None:
            raise RuntimeError("Session has not been started")
        return self._context

    def __enter__(self) -> "TikTokSession":
        self._playwright = sync_playwright().start()
        browser = self._playwright.chromium.launch(headless=self.config.headless)
        kwargs = {
            "viewport": {"width": 1366, "height": 2000},
            "user_agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "locale": "en-US",
        }
        if self.config.storage_state_path:
            kwargs["storage_state"] = self.config.storage_state_path
        self._context = browser.new_context(**kwargs)
        self._context.set_default_timeout(self.config.timeout_ms)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._context:
            try:
                self._context.browser.close()
            finally:
                self._context = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def new_page(self) -> Page:
        return self.context.new_page()

    def human_delay(self) -> None:
        time.sleep(random.uniform(self.config.min_delay_s, self.config.max_delay_s))

    def with_retry(self, fn: Callable[[], object], retries: int = 3) -> object:
        last_exc: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                return fn()
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt == retries:
                    break
                self.human_delay()
        if last_exc:
            raise last_exc
        raise RuntimeError("Unexpected retry flow")
