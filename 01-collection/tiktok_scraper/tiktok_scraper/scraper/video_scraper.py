from __future__ import annotations

import json
import re
from typing import Any

from playwright.sync_api import Page

from ..models import VideoItem
from .parsing import coerce_int, parse_timestamp
from .session import TikTokSession


class VideoScraper:
    def __init__(self, session: TikTokSession) -> None:
        self.session = session

    def scrape_video(self, account_username: str, video_url: str) -> VideoItem:
        page = self.session.new_page()
        self.session.with_retry(
            lambda: page.goto(video_url, wait_until="domcontentloaded")
        )
        page.wait_for_timeout(2000)
        self.session.human_delay()

        payload = self._extract_sigistate_json(page)
        item = self._to_video_item(
            payload, account_username=account_username, video_url=video_url
        )
        page.close()
        return item

    def _extract_sigistate_json(self, page: Page) -> dict[str, Any]:
        script = page.locator("#SIGI_STATE")
        if script.count() == 0:
            return {}
        raw_json = script.first.inner_text()
        if not raw_json:
            return {}
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError:
            return {}

    def _to_video_item(
        self, payload: dict[str, Any], *, account_username: str, video_url: str
    ) -> VideoItem:
        item_info = _dig(payload, ["ItemModule"]) or {}
        video_id = _video_id_from_url(video_url)
        candidate = item_info.get(video_id) if isinstance(item_info, dict) else None
        if not isinstance(candidate, dict):
            candidate = _find_video_module_candidate(
                item_info, fallback_video_id=video_id
            )
        stats = candidate.get("stats", {}) if isinstance(candidate, dict) else {}
        video_meta = candidate.get("video", {}) if isinstance(candidate, dict) else {}
        author = candidate.get("authorStats", {}) if isinstance(candidate, dict) else {}
        music = candidate.get("music", {}) if isinstance(candidate, dict) else {}

        desc = candidate.get("desc") if isinstance(candidate, dict) else None
        hashtags = re.findall(r"#(\w+)", desc or "")
        mentions = re.findall(r"@(\w+)", desc or "")

        return VideoItem(
            account_username=account_username,
            video_id=video_id,
            video_url=video_url,
            description=desc,
            create_time=parse_timestamp(
                candidate.get("createTime") if isinstance(candidate, dict) else None
            ),
            duration_seconds=coerce_int(video_meta.get("duration")),
            view_count=coerce_int(stats.get("playCount")),
            like_count=coerce_int(stats.get("diggCount")),
            comment_count=coerce_int(stats.get("commentCount")),
            share_count=coerce_int(stats.get("shareCount")),
            hashtags=hashtags,
            mentions=mentions,
            language=candidate.get("language") if isinstance(candidate, dict) else None,
            is_pinned=bool(candidate.get("isPinned"))
            if isinstance(candidate, dict)
            else None,
            video_play_url=video_meta.get("playAddr"),
            cover_url=video_meta.get("cover"),
            music_url=music.get("playUrl"),
            music_title=music.get("title"),
            music_author=music.get("authorName"),
            author_display_name=candidate.get("nickname")
            if isinstance(candidate, dict)
            else None,
            author_follower_count=coerce_int(author.get("followerCount")),
            raw=candidate if isinstance(candidate, dict) else {},
        )


def _dig(data: dict[str, Any], keys: list[str]) -> Any:
    cursor: Any = data
    for key in keys:
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(key)
    return cursor


def _video_id_from_url(url: str) -> str:
    match = re.search(r"/video/(\d+)", url)
    if not match:
        raise ValueError(f"Could not parse video id from url: {url}")
    return match.group(1)


def _find_video_module_candidate(
    module: Any, *, fallback_video_id: str
) -> dict[str, Any]:
    if not isinstance(module, dict):
        return {}
    if fallback_video_id in module and isinstance(module[fallback_video_id], dict):
        return module[fallback_video_id]
    for value in module.values():
        if isinstance(value, dict):
            maybe_id = str(value.get("id", ""))
            if maybe_id == fallback_video_id:
                return value
    return {}
