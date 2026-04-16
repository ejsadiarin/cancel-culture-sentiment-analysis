from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse
from typing import Any

from ..models import AccountSnapshot
from .yt_dlp_client import YtDlpClient


class ChannelScraper:
    def __init__(self, client: YtDlpClient) -> None:
        self.client = client

    def scrape_anchor(self, anchor_url: str) -> tuple[dict[str, Any], AccountSnapshot]:
        payload = self.client.dump_json(anchor_url)
        channel_id = str(payload.get("channel_id") or payload.get("uploader_id") or "")
        channel_url = resolve_channel_url(payload)
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

    def list_uploads(
        self, channel_url: str, *, playlist_end: int = 50
    ) -> list[dict[str, Any]]:
        uploads_url = _ensure_videos_url(channel_url)
        return self.client.dump_json_entries(
            uploads_url,
            flat=False,
            playlist_end=playlist_end,
        )


def _normalize_handle(value: object) -> str | None:
    text = _as_str(value)
    if not text:
        return None
    return text.lstrip("@")


def _as_int(value: object) -> int | None:
    if value is None:
        return None
    if not isinstance(value, (int, float, str)):
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


def resolve_channel_url(payload: dict[str, Any]) -> str | None:
    channel_url = _as_str(payload.get("channel_url")) or _as_str(
        payload.get("uploader_url")
    )
    if channel_url:
        return _ensure_videos_url(channel_url)
    channel_id = _as_str(payload.get("channel_id")) or _as_str(
        payload.get("uploader_id")
    )
    if channel_id:
        return _ensure_videos_url(f"https://www.youtube.com/channel/{channel_id}")
    handle = _normalize_handle(payload.get("uploader"))
    if handle:
        return _ensure_videos_url(f"https://www.youtube.com/@{handle}")
    return None


def _ensure_videos_url(url: str) -> str:
    trimmed = url.strip()
    if not trimmed:
        return url
    if "://" not in trimmed:
        trimmed = f"https://www.youtube.com/{trimmed.lstrip('/')}"
    parsed = urlparse(trimmed)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc or "www.youtube.com"
    path = parsed.path.rstrip("/")
    if not path:
        return urlunparse((scheme, netloc, "/videos", "", "", ""))
    segments = [segment for segment in path.split("/") if segment]
    if any(segment in {"videos", "streams", "shorts"} for segment in segments):
        new_path = "/" + "/".join(segments)
    else:
        if len(segments) >= 2 and segments[0] in {"channel", "c", "user"}:
            base = "/" + "/".join(segments[:2])
            if len(segments) >= 3:
                base = "/" + "/".join(segments[:3])
        else:
            base = "/" + "/".join(segments[:1])
        new_path = base.rstrip("/") + "/videos"
    return urlunparse((scheme, netloc, new_path, "", "", ""))
