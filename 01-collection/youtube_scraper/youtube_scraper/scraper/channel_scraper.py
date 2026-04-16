from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..models import AccountSnapshot
from .yt_dlp_client import YtDlpClient


class ChannelScraper:
    def __init__(self, client: YtDlpClient) -> None:
        self.client = client

    def scrape_anchor(self, anchor_url: str) -> tuple[dict[str, Any], AccountSnapshot]:
        payload = self.client.dump_json(anchor_url)
        channel_id = str(payload.get("channel_id") or payload.get("uploader_id") or "")
        channel_url = _as_str(payload.get("channel_url"))
        snapshot = AccountSnapshot(
            channel_id=channel_id,
            channel_handle=_normalize_handle(payload.get("uploader")),
            display_name=_as_str(payload.get("channel"))
            or _as_str(payload.get("uploader")),
            description=_as_str(payload.get("uploader_description")),
            followers=_as_int(payload.get("channel_follower_count")),
            total_views=_as_int(payload.get("channel_view_count")),
            video_count=_as_int(payload.get("channel_video_count")),
            scrape_url=channel_url,
        )
        return payload, snapshot

    def list_uploads(self, channel_url: str) -> list[dict[str, Any]]:
        return self.client.dump_json_entries(channel_url)


def _normalize_handle(value: object) -> str | None:
    text = _as_str(value)
    if not text:
        return None
    return text.lstrip("@")


def _as_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_upload_date(value: object) -> datetime | None:
    if not value:
        return None
    text = str(value)
    try:
        parsed = datetime.strptime(text, "%Y%m%d")
        return parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
