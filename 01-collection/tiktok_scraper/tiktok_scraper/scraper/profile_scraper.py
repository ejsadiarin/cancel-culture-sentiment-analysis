from __future__ import annotations

import re
from dataclasses import dataclass

from playwright.sync_api import Page

from ..models import AccountSnapshot
from .parsing import coerce_int
from .session import TikTokSession


@dataclass(slots=True)
class ProfileScrapeResult:
    account: AccountSnapshot
    video_urls: list[str]


class ProfileScraper:
    def __init__(
        self, session: TikTokSession, *, max_videos: int, scroll_limit: int = 120
    ) -> None:
        self.session = session
        self.max_videos = max_videos
        self.scroll_limit = scroll_limit

    def scrape(self, username: str) -> ProfileScrapeResult:
        page = self.session.new_page()
        profile_url = f"https://www.tiktok.com/@{username}"
        self.session.with_retry(
            lambda: page.goto(profile_url, wait_until="domcontentloaded")
        )
        page.wait_for_timeout(2200)
        self.session.human_delay()

        account = self._extract_account(
            page, username=username, profile_url=profile_url
        )
        video_urls = self._discover_video_urls(page, username=username)
        page.close()

        return ProfileScrapeResult(account=account, video_urls=video_urls)

    def _extract_account(
        self, page: Page, *, username: str, profile_url: str
    ) -> AccountSnapshot:
        def text(selector: str) -> str | None:
            loc = page.locator(selector)
            if loc.count() == 0:
                return None
            value = loc.first.inner_text().strip()
            return value or None

        display_name = text("h1[data-e2e='user-title']")
        bio = text("h2[data-e2e='user-bio']")
        followers = coerce_int(text("strong[data-e2e='followers-count']"))
        following = coerce_int(text("strong[data-e2e='following-count']"))
        likes = coerce_int(text("strong[data-e2e='likes-count']"))

        return AccountSnapshot(
            username=username,
            display_name=display_name,
            bio=bio,
            followers=followers,
            following=following,
            likes=likes,
            scrape_url=profile_url,
        )

    def _discover_video_urls(self, page: Page, *, username: str) -> list[str]:
        links: set[str] = set()
        stable_rounds = 0

        for _ in range(self.scroll_limit):
            hrefs: list[str] = page.eval_on_selector_all(
                "a[href*='/video/']",
                "nodes => nodes.map(node => node.href)",
            )
            for href in hrefs:
                if f"/@{username}/video/" in href:
                    links.add(_normalize_video_url(href))

            if len(links) >= self.max_videos:
                break

            prev_count = len(links)
            page.mouse.wheel(0, 6000)
            page.wait_for_timeout(1500)
            self.session.human_delay()
            if len(links) == prev_count:
                stable_rounds += 1
            else:
                stable_rounds = 0
            if stable_rounds >= 6:
                break

        urls = sorted(links)
        return urls[: self.max_videos]


def _normalize_video_url(url: str) -> str:
    match = re.search(r"(https://www\.tiktok\.com/@[^/]+/video/\d+)", url)
    if match:
        return match.group(1)
    return url.split("?")[0]
