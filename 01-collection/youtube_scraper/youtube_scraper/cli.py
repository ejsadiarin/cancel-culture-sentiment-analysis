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

    anchor_payload, account_snapshot = channel_scraper.scrape_anchor(config.anchor_url)
    anchor_video_id = str(anchor_payload.get("id") or "")
    anchor_date = parse_upload_date(anchor_payload.get("upload_date"))
    channel_url = anchor_payload.get("channel_url") or anchor_payload.get(
        "uploader_url"
    )

    if not anchor_video_id or not anchor_date or not channel_url:
        raise ValueError("Unable to resolve anchor video, date, or channel URL")

    writer.write(account_snapshot.to_record(run_id=run_id, scraped_at=scraped_at))

    window_map = _build_windows(anchor_date, config)
    uploads = channel_scraper.list_uploads(str(channel_url))

    total_videos = 0
    total_comments = 0
    failures = 0

    for window_label, (start, end) in window_map.items():
        selected = _select_uploads(uploads, start, end, config.max_videos_per_window)
        LOGGER.info(
            "Window %s range=%s..%s selected=%d",
            window_label,
            start.date(),
            end.date(),
            len(selected),
        )
        for entry in selected:
            video_url = entry.get("url") or entry.get("webpage_url")
            if not video_url:
                continue
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
    uploads: list[dict[str, object]],
    start: datetime,
    end: datetime,
    limit: int,
) -> list[dict[str, object]]:
    candidates: list[tuple[datetime, dict[str, object]]] = []
    for entry in uploads:
        if not isinstance(entry, dict):
            continue
        upload_date = parse_upload_date(entry.get("upload_date"))
        if not upload_date:
            continue
        if start <= upload_date <= end:
            candidates.append((upload_date, entry))
    candidates.sort(key=lambda item: item[0])
    return [entry for _, entry in candidates[:limit]]


def main() -> int:
    config = parse_args(sys.argv[1:])
    return run(config)


if __name__ == "__main__":
    raise SystemExit(main())
