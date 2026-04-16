from __future__ import annotations

import argparse
import logging
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import CommentItem, VideoItem
from .scraper.channel_scraper import ChannelScraper, parse_upload_date
from .scraper.comment_scraper import CommentScraper
from .scraper.video_scraper import VideoScraper
from .scraper.yt_dlp_client import YtDlpClient
from .storage.jsonl_writer import JsonlWriter

LOGGER = logging.getLogger("youtube_scraper")


@dataclass(slots=True)
class RunConfig:
    anchor_url: str
    output_path: str
    pre_days: int
    cancel_days: int
    post_days: int
    max_videos_per_window: int
    max_comments_per_video: int
    cache_dir: str | None
    comments_dir: str
    playlist_end: int


def parse_args(argv: list[str]) -> RunConfig:
    parser = argparse.ArgumentParser(
        description="Scrape YouTube apology anchor with pre/post windows"
    )
    parser.add_argument("--anchor-url", required=True, help="YouTube video URL")
    parser.add_argument(
        "--out",
        default="data/raw/youtube_anchor.jsonl",
        help="Output JSONL path",
    )
    parser.add_argument("--pre-days", type=int, default=30)
    parser.add_argument("--cancel-days", type=int, default=7)
    parser.add_argument("--post-days", type=int, default=30)
    parser.add_argument("--max-videos-per-window", type=int, default=50)
    parser.add_argument("--max-comments-per-video", type=int, default=1000)
    parser.add_argument(
        "--playlist-end",
        type=int,
        default=50,
        help="Max uploads to scan from channel feed",
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Optional yt-dlp cache directory",
    )
    parser.add_argument(
        "--comments-dir",
        default="data/raw/youtube_comments",
        help="Directory to store yt-dlp comment dumps",
    )
    parser.add_argument("--log-level", default="INFO")

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    return RunConfig(
        anchor_url=args.anchor_url,
        output_path=args.out,
        pre_days=max(1, int(args.pre_days)),
        cancel_days=max(1, int(args.cancel_days)),
        post_days=max(1, int(args.post_days)),
        max_videos_per_window=max(1, int(args.max_videos_per_window)),
        max_comments_per_video=int(args.max_comments_per_video),
        cache_dir=args.cache_dir,
        comments_dir=args.comments_dir,
        playlist_end=max(1, int(args.playlist_end)),
    )


def run(config: RunConfig) -> int:
    run_id = uuid.uuid4().hex
    scraped_at = datetime.now(timezone.utc).isoformat()
    Path(config.output_path).parent.mkdir(parents=True, exist_ok=True)

    client = YtDlpClient(cache_dir=config.cache_dir)
    channel_scraper = ChannelScraper(client)
    video_scraper = VideoScraper(client)
    comment_scraper = CommentScraper(
        client, max_comments_per_video=config.max_comments_per_video
    )
    writer = JsonlWriter(config.output_path)

    LOGGER.info("Starting run_id=%s anchor=%s", run_id, config.anchor_url)

    LOGGER.info("Resolving anchor metadata")

    anchor_payload, account_snapshot = channel_scraper.scrape_anchor(config.anchor_url)
    anchor_video_id = str(anchor_payload.get("id") or "")
    anchor_date = parse_upload_date(anchor_payload.get("upload_date"))
    channel_url = (
        account_snapshot.scrape_url
        or anchor_payload.get("channel_url")
        or anchor_payload.get("uploader_url")
    )

    if not anchor_video_id or not anchor_date or not channel_url:
        raise ValueError("Unable to resolve anchor video, date, or channel URL")

    writer.write(account_snapshot.to_record(run_id=run_id, scraped_at=scraped_at))

    window_map = _build_windows(anchor_date, config)
    LOGGER.info("Listing channel uploads")
    uploads = channel_scraper.list_uploads(
        str(channel_url),
        playlist_end=config.playlist_end,
    )
    if uploads:
        sample = uploads[0]
        LOGGER.debug(
            "Upload sample keys=%s",
            ",".join(sorted(sample.keys())) if isinstance(sample, dict) else "",
        )
    earliest_start = min(start for start, _ in window_map.values())
    latest_end = max(end for _, end in window_map.values())
    run_year = anchor_date.year
    uploads_with_dates = _resolve_upload_dates(
        uploads,
        earliest_start=earliest_start,
        latest_end=latest_end,
        run_year=run_year,
        video_scraper=video_scraper,
        channel_id=account_snapshot.channel_id,
    )
    LOGGER.info(
        "Resolved upload dates %d/%d",
        len(uploads_with_dates),
        len(uploads),
    )

    total_videos = 0
    total_comments = 0
    failures = 0

    for window_label, (start, end) in window_map.items():
        selected = _select_uploads(
            uploads_with_dates,
            start,
            end,
            config.max_videos_per_window,
        )
        LOGGER.info(
            "Window %s range=%s..%s selected=%d",
            window_label,
            start.date(),
            end.date(),
            len(selected),
        )
        total_selected = len(selected)
        for index, entry in enumerate(selected, start=1):
            video_url = entry.get("url") or entry.get("webpage_url")
            if not video_url:
                continue
            remaining = max(total_selected - index, 0)
            LOGGER.info(
                "Scraping video %d/%d window=%s remaining=%d",
                index,
                total_selected,
                window_label,
                remaining,
            )
            try:
                video = video_scraper.scrape_video(
                    account_snapshot.channel_id,
                    str(video_url),
                    window_label=window_label,
                    anchor_id=anchor_video_id,
                )
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("Video scrape failed %s: %s", video_url, exc)
                failures += 1
                continue

            if writer.write(video.to_record(run_id=run_id, scraped_at=scraped_at)):
                total_videos += 1

            try:
                comments = comment_scraper.scrape_comments(
                    account_snapshot.channel_id,
                    video.video_id,
                    video.video_url,
                    window_label=window_label,
                    anchor_id=anchor_video_id,
                    output_dir=config.comments_dir,
                )
                for comment in comments:
                    if writer.write(
                        comment.to_record(run_id=run_id, scraped_at=scraped_at)
                    ):
                        total_comments += 1
                LOGGER.info(
                    "Comments scraped video=%s count=%d", video.video_id, len(comments)
                )
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("Comments scrape failed %s: %s", video.video_id, exc)
                failures += 1

    writer.close()
    LOGGER.info(
        "Done run_id=%s videos=%d comments=%d failures=%d output=%s",
        run_id,
        total_videos,
        total_comments,
        failures,
        config.output_path,
    )
    return 0 if total_videos > 0 else 1


def _build_windows(
    anchor_date: datetime, config: RunConfig
) -> dict[str, tuple[datetime, datetime]]:
    anchor_day = anchor_date.astimezone(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    pre_start = anchor_day - timedelta(days=config.pre_days)
    pre_end = anchor_day - timedelta(days=1)
    cancel_start = anchor_day
    cancel_end = anchor_day + timedelta(days=config.cancel_days)
    post_start = anchor_day + timedelta(days=config.cancel_days + 1)
    post_end = anchor_day + timedelta(days=config.cancel_days + config.post_days)
    return {
        "pre": (pre_start, pre_end),
        "cancel": (cancel_start, cancel_end),
        "post": (post_start, post_end),
    }


def _select_uploads(
    uploads: list[tuple[datetime, dict[str, object]]],
    start: datetime,
    end: datetime,
    limit: int,
) -> list[dict[str, object]]:
    candidates: list[tuple[datetime, dict[str, object]]] = []
    for upload_date, entry in uploads:
        if start <= upload_date <= end:
            candidates.append((upload_date, entry))
    candidates.sort(key=lambda item: item[0])
    return [entry for _, entry in candidates[:limit]]


def _resolve_upload_dates(
    uploads: list[dict[str, object]],
    *,
    earliest_start: datetime,
    latest_end: datetime,
    run_year: int,
    video_scraper: VideoScraper,
    channel_id: str,
) -> list[tuple[datetime, dict[str, object]]]:
    resolved: list[tuple[datetime, dict[str, object]]] = []
    cache: dict[str, datetime | None] = {}
    scanned = 0
    total = len(uploads)
    for entry in uploads:
        if not isinstance(entry, dict):
            continue
        scanned += 1
        remaining = max(total - scanned, 0)
        LOGGER.info(
            "Resolving upload dates %d/%d remaining=%d", scanned, total, remaining
        )
        cache_key = _cache_key(entry)
        if cache_key in cache:
            upload_date = cache[cache_key]
        else:
            upload_date = _resolve_upload_datetime(
                entry,
                video_scraper=video_scraper,
                channel_id=channel_id,
            )
            cache[cache_key] = upload_date
        if upload_date:
            upload_date = _normalize_upload_date(
                upload_date,
                run_year=run_year,
            )
            LOGGER.debug("Resolved %s -> %s", cache_key, upload_date.date())
        else:
            LOGGER.debug("Unresolved %s", cache_key)
        if upload_date and earliest_start <= upload_date <= latest_end:
            resolved.append((upload_date, entry))
    LOGGER.info("Resolved uploads scanned=%d resolved=%d", scanned, len(resolved))
    return resolved


def _normalize_upload_date(upload_date: datetime, *, run_year: int) -> datetime:
    if upload_date.year > run_year:
        return upload_date.replace(year=run_year)
    return upload_date


def _resolve_upload_datetime(
    entry: dict[str, object],
    *,
    video_scraper: VideoScraper,
    channel_id: str,
) -> datetime | None:
    upload_date = parse_upload_date(entry.get("upload_date"))
    if upload_date:
        return upload_date
    upload_date = _parse_timestamp(
        entry.get("timestamp")
        or entry.get("release_timestamp")
        or entry.get("release_time")
    )
    if upload_date:
        return upload_date
    video_url = _extract_video_url(entry)
    if not video_url:
        return None
    try:
        video = video_scraper.scrape_video(channel_id, video_url)
    except Exception as exc:  # noqa: BLE001
        LOGGER.debug("Upload date resolve failed %s: %s", video_url, exc)
        return None
    return video.create_time


def _cache_key(entry: dict[str, object]) -> str:
    candidate = entry.get("id") or entry.get("webpage_url") or entry.get("url")
    if not candidate:
        return "__unknown__"
    return str(candidate).strip() or "__unknown__"


def _parse_timestamp(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, (int, float, str)):
        return None
    try:
        timestamp = float(value)
    except (TypeError, ValueError, OSError):
        return None
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def _extract_video_url(entry: dict[str, object]) -> str | None:
    candidate = entry.get("webpage_url") or entry.get("url") or entry.get("id")
    if not candidate:
        return None
    text = str(candidate).strip()
    if not text:
        return None
    if text.startswith("http"):
        return text
    return f"https://www.youtube.com/watch?v={text}"


def main() -> int:
    config = parse_args(sys.argv[1:])
    return run(config)


if __name__ == "__main__":
    raise SystemExit(main())
