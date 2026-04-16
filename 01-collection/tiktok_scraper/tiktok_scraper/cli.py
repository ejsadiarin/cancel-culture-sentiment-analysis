from __future__ import annotations

import argparse
import logging
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .filters.timeframe import DateRange, build_date_range
from .models import VideoItem
from .scraper.comment_scraper import CommentScraper
from .scraper.profile_scraper import ProfileScraper
from .scraper.session import SessionConfig, TikTokSession
from .scraper.video_scraper import VideoScraper
from .storage.jsonl_writer import JsonlWriter
from .transcription.whisper_transcriber import WhisperTranscriber

LOGGER = logging.getLogger("tiktok_scraper")


@dataclass(slots=True)
class RunConfig:
    accounts: list[str]
    date_range: DateRange
    output_path: str
    max_videos: int
    max_comments_per_video: int
    headless: bool
    cookie_file: str | None
    timeout_ms: int
    min_delay_s: float
    max_delay_s: float
    transcribe: bool
    transcription_model: str


def parse_args(argv: list[str]) -> RunConfig:
    parser = argparse.ArgumentParser(
        description="Scrape TikTok accounts by timeframe and export JSONL"
    )
    parser.add_argument(
        "--account", action="append", required=True, help="TikTok username (repeatable)"
    )
    parser.add_argument("--start-date", required=True, help="Start date in YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="End date in YYYY-MM-DD")
    parser.add_argument(
        "--out",
        default="data/raw/tiktok_scrape.jsonl",
        help="Output JSONL path",
    )
    parser.add_argument("--max-videos", type=int, default=500)
    parser.add_argument("--max-comments-per-video", type=int, default=5000)
    parser.add_argument(
        "--headless", action=argparse.BooleanOptionalAction, default=True
    )
    parser.add_argument(
        "--cookie-file", default=None, help="Playwright storage state JSON path"
    )
    parser.add_argument("--timeout-ms", type=int, default=45000)
    parser.add_argument("--min-delay", type=float, default=0.8)
    parser.add_argument("--max-delay", type=float, default=2.2)
    parser.add_argument(
        "--transcribe", action=argparse.BooleanOptionalAction, default=False
    )
    parser.add_argument("--transcription-model", default="small")
    parser.add_argument("--log-level", default="INFO")

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    date_range = build_date_range(args.start_date, args.end_date)

    return RunConfig(
        accounts=[a.strip().lstrip("@") for a in args.account],
        date_range=date_range,
        output_path=args.out,
        max_videos=args.max_videos,
        max_comments_per_video=args.max_comments_per_video,
        headless=bool(args.headless),
        cookie_file=args.cookie_file,
        timeout_ms=args.timeout_ms,
        min_delay_s=args.min_delay,
        max_delay_s=args.max_delay,
        transcribe=bool(args.transcribe),
        transcription_model=args.transcription_model,
    )


def run(config: RunConfig) -> int:
    run_id = uuid.uuid4().hex
    scraped_at = datetime.now(timezone.utc).isoformat()
    Path(config.output_path).parent.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Starting run_id=%s accounts=%s", run_id, ",".join(config.accounts))
    writer = JsonlWriter(config.output_path)

    session_config = SessionConfig(
        headless=config.headless,
        storage_state_path=config.cookie_file,
        timeout_ms=config.timeout_ms,
        min_delay_s=config.min_delay_s,
        max_delay_s=config.max_delay_s,
    )

    total_videos = 0
    total_comments = 0
    total_transcripts = 0
    failures = 0

    with TikTokSession(session_config) as session:
        profile_scraper = ProfileScraper(session, max_videos=config.max_videos)
        video_scraper = VideoScraper(session)
        comment_scraper = CommentScraper(
            session, max_comments_per_video=config.max_comments_per_video
        )
        transcriber = (
            WhisperTranscriber(model_name=config.transcription_model)
            if config.transcribe
            else None
        )

        for account in config.accounts:
            LOGGER.info("Collecting profile @%s", account)
            try:
                profile = profile_scraper.scrape(account)
                writer.write(
                    profile.account.to_record(run_id=run_id, scraped_at=scraped_at)
                )
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("Failed profile scrape @%s: %s", account, exc)
                failures += 1
                continue

            in_range_video_urls: list[str] = []
            staged_video_items: dict[str, VideoItem] = {}
            for video_url in profile.video_urls:
                try:
                    video = video_scraper.scrape_video(account, video_url)
                except Exception as exc:  # noqa: BLE001
                    LOGGER.warning("Video scrape failed %s: %s", video_url, exc)
                    failures += 1
                    continue
                if not config.date_range.includes(video.create_time):
                    continue
                staged_video_items[video.video_id] = video
                in_range_video_urls.append(video_url)

            LOGGER.info(
                "Account @%s discovered=%d in_range=%d",
                account,
                len(profile.video_urls),
                len(in_range_video_urls),
            )

            for video_url in in_range_video_urls:
                video_id = video_url.rsplit("/", 1)[-1]
                video = staged_video_items.get(video_id)
                if not video:
                    continue
                if writer.write(video.to_record(run_id=run_id, scraped_at=scraped_at)):
                    total_videos += 1

                try:
                    comments = comment_scraper.scrape_comments(
                        account, video_url, video.video_id
                    )
                    for comment in comments:
                        if writer.write(
                            comment.to_record(run_id=run_id, scraped_at=scraped_at)
                        ):
                            total_comments += 1
                except Exception as exc:  # noqa: BLE001
                    LOGGER.warning(
                        "Comments scrape failed for %s: %s", video.video_id, exc
                    )
                    failures += 1

                if transcriber:
                    try:
                        transcript = transcriber.transcribe_video(
                            account_username=account,
                            video_id=video.video_id,
                            video_url=video.video_play_url,
                            language=video.language,
                        )
                        if transcript and writer.write(
                            transcript.to_record(run_id=run_id, scraped_at=scraped_at)
                        ):
                            total_transcripts += 1
                    except Exception as exc:  # noqa: BLE001
                        LOGGER.warning(
                            "Transcription failed for %s: %s", video.video_id, exc
                        )
                        failures += 1

    writer.close()

    LOGGER.info(
        "Done run_id=%s videos=%d comments=%d transcripts=%d failures=%d output=%s",
        run_id,
        total_videos,
        total_comments,
        total_transcripts,
        failures,
        config.output_path,
    )
    return 0 if total_videos > 0 else 1


def main() -> int:
    config = parse_args(sys.argv[1:])
    return run(config)


if __name__ == "__main__":
    raise SystemExit(main())
