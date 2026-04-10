from __future__ import annotations

import argparse
import getpass
import logging
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import instaloader
from instaloader import exceptions as ig_exceptions

from .filters.timeframe import DateRange, build_date_range
from .scraper.comment_scraper import CommentScraper
from .scraper.post_scraper import PostScraper
from .scraper.profile_scraper import ProfileScraper
from .scraper.session import InstagramSession, SessionConfig
from .storage.jsonl_writer import JsonlWriter

LOGGER = logging.getLogger("instagram_scraper")


@dataclass(slots=True)
class RunConfig:
    accounts: list[str]
    post_shortcodes: list[str]
    date_range: DateRange
    output_path: str
    max_posts: int
    max_comments_per_post: int
    session_file: str | None
    session_user: str | None
    allow_anonymous: bool
    login_user: str | None
    login_password_env: str
    min_delay_s: float
    max_delay_s: float
    max_retries: int


def parse_args(argv: list[str]) -> RunConfig:
    parser = argparse.ArgumentParser(
        description="Scrape Instagram accounts by timeframe and export JSONL"
    )
    parser.add_argument(
        "--account",
        action="append",
        default=[],
        help="Instagram username (repeatable)",
    )
    parser.add_argument(
        "--shortcode",
        action="append",
        default=[],
        help="Instagram post shortcode (repeatable)",
    )
    parser.add_argument(
        "--post-url",
        action="append",
        default=[],
        help="Instagram post URL like https://www.instagram.com/p/SHORTCODE/ (repeatable)",
    )
    parser.add_argument("--start-date", required=True, help="Start date in YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="End date in YYYY-MM-DD")
    parser.add_argument("--out", required=True, help="Output JSONL path")
    parser.add_argument("--max-posts", type=int, default=400)
    parser.add_argument("--max-comments-per-post", type=int, default=3000)
    parser.add_argument(
        "--session-file",
        default="01-collection/instagram_scraper/.ig_session",
        help="Session file path used to persist authenticated login",
    )
    parser.add_argument(
        "--session-user",
        default=None,
        help="Instagram username associated with --session-file",
    )
    parser.add_argument(
        "--allow-anonymous",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Allow unauthenticated scraping when session/login is unavailable",
    )
    parser.add_argument(
        "--login-user",
        default=None,
        help="Instagram username to log in and save session",
    )
    parser.add_argument(
        "--login-password-env",
        default="INSTAGRAM_PASSWORD",
        help="Environment variable name containing login password",
    )
    parser.add_argument("--min-delay", type=float, default=1.4)
    parser.add_argument("--max-delay", type=float, default=3.2)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--log-level", default="INFO")

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    date_range = build_date_range(args.start_date, args.end_date)
    post_shortcodes = [_normalize_shortcode(s) for s in args.shortcode]
    post_shortcodes.extend(_extract_shortcode_from_url(url) for url in args.post_url)
    post_shortcodes = sorted({s for s in post_shortcodes if s})

    accounts = [a.strip().lstrip("@") for a in args.account if a and a.strip()]
    if not accounts and not post_shortcodes:
        raise ValueError("provide at least one --account, --shortcode, or --post-url")

    return RunConfig(
        accounts=accounts,
        post_shortcodes=post_shortcodes,
        date_range=date_range,
        output_path=args.out,
        max_posts=max(1, int(args.max_posts)),
        max_comments_per_post=int(args.max_comments_per_post),
        session_file=args.session_file,
        session_user=args.session_user,
        allow_anonymous=bool(args.allow_anonymous),
        login_user=args.login_user,
        login_password_env=args.login_password_env,
        min_delay_s=float(args.min_delay),
        max_delay_s=float(args.max_delay),
        max_retries=max(1, int(args.max_retries)),
    )


def build_loader() -> instaloader.Instaloader:
    return instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
        iphone_support=False,
    )


def _load_or_login(loader: instaloader.Instaloader, config: RunConfig) -> bool:
    session_file = (
        Path(config.session_file).expanduser() if config.session_file else None
    )

    if session_file and session_file.exists() and config.session_user:
        try:
            loader.load_session_from_file(config.session_user, str(session_file))
            LOGGER.info("Loaded session file for user=%s", config.session_user)
            return True
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Failed to load existing session file: %s", exc)

    if config.login_user:
        password = os.getenv(config.login_password_env)
        if not password:
            password = getpass.getpass(f"Instagram password for {config.login_user}: ")
        try:
            loader.login(config.login_user, password)
            if session_file:
                session_file.parent.mkdir(parents=True, exist_ok=True)
                loader.save_session_to_file(str(session_file))
                LOGGER.info("Saved authenticated session to %s", session_file)
            return True
        except ig_exceptions.BadCredentialsException:
            LOGGER.error("Instagram login failed: bad credentials")
            return False
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Instagram login failed: %s", exc)
            return False

    if config.allow_anonymous:
        LOGGER.warning(
            "Running in anonymous mode; risk of blocks and missing comments is higher"
        )
        return False

    raise ValueError(
        "Authentication required: provide --session-user with an existing --session-file, "
        "or pass --login-user, or explicitly allow --allow-anonymous"
    )


def run(config: RunConfig) -> int:
    if config.max_delay_s < config.min_delay_s:
        raise ValueError("max-delay must be greater than or equal to min-delay")

    run_id = uuid.uuid4().hex
    scraped_at = datetime.now(timezone.utc).isoformat()
    Path(config.output_path).parent.mkdir(parents=True, exist_ok=True)

    LOGGER.info(
        "Starting run_id=%s accounts=%s shortcodes=%s",
        run_id,
        ",".join(config.accounts),
        ",".join(config.post_shortcodes),
    )
    writer = JsonlWriter(config.output_path)

    loader = build_loader()
    _load_or_login(loader, config)

    session = InstagramSession(
        SessionConfig(
            min_delay_s=config.min_delay_s,
            max_delay_s=config.max_delay_s,
            max_retries=config.max_retries,
        ),
        loader,
    )

    profile_scraper = ProfileScraper(session, max_posts=config.max_posts)
    post_scraper = PostScraper()
    comment_scraper = CommentScraper(max_comments_per_post=config.max_comments_per_post)

    total_posts = 0
    total_comments = 0
    failures = 0

    for shortcode in config.post_shortcodes:
        LOGGER.info("Collecting post shortcode=%s", shortcode)
        try:
            post = session.with_retry(
                lambda s=shortcode: instaloader.Post.from_shortcode(loader.context, s)
            )
            owner_profile = getattr(post, "owner_profile", None)
            source_account = (
                getattr(owner_profile, "username", None)
                or getattr(post, "owner_username", None)
                or "unknown"
            )
            post_item = post_scraper.to_post_item(source_account, post)

            if config.date_range.includes(post_item.create_time):
                if writer.write(
                    post_item.to_record(run_id=run_id, scraped_at=scraped_at)
                ):
                    total_posts += 1
                session.human_delay()

                comments = session.with_retry(
                    lambda p=post, a=source_account: comment_scraper.scrape_comments(
                        a, p
                    )
                )
                for comment in comments:
                    if writer.write(
                        comment.to_record(run_id=run_id, scraped_at=scraped_at)
                    ):
                        total_comments += 1
                session.human_delay()
            else:
                LOGGER.info("Skipping shortcode=%s outside date range", shortcode)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Failed shortcode=%s: %s", shortcode, exc)
            failures += 1

    for account in config.accounts:
        LOGGER.info("Collecting profile @%s", account)
        try:
            profile_data = session.with_retry(lambda: profile_scraper.scrape(account))
            writer.write(
                profile_data.account.to_record(run_id=run_id, scraped_at=scraped_at)
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Failed profile scrape @%s: %s", account, exc)
            failures += 1
            continue

        in_range_posts = []
        for post in profile_data.posts:
            try:
                post_item = post_scraper.to_post_item(account, post)
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning(
                    "Post parse failed %s: %s", getattr(post, "shortcode", "?"), exc
                )
                failures += 1
                continue

            if not config.date_range.includes(post_item.create_time):
                continue
            in_range_posts.append((post, post_item))

        LOGGER.info(
            "Account @%s discovered=%d in_range=%d",
            account,
            len(profile_data.posts),
            len(in_range_posts),
        )

        for post, post_item in in_range_posts:
            if writer.write(post_item.to_record(run_id=run_id, scraped_at=scraped_at)):
                total_posts += 1
            session.human_delay()

            try:
                comments = session.with_retry(
                    lambda: comment_scraper.scrape_comments(account, post)
                )
                for comment in comments:
                    if writer.write(
                        comment.to_record(run_id=run_id, scraped_at=scraped_at)
                    ):
                        total_comments += 1
                session.human_delay()
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning(
                    "Comment scrape failed for %s: %s", post_item.post_shortcode, exc
                )
                failures += 1

    writer.close()

    LOGGER.info(
        "Done run_id=%s posts=%d comments=%d failures=%d output=%s",
        run_id,
        total_posts,
        total_comments,
        failures,
        config.output_path,
    )
    return 0 if total_posts > 0 else 1


def main() -> int:
    config = parse_args(sys.argv[1:])
    return run(config)


def _normalize_shortcode(value: str) -> str:
    return value.strip().strip("/")


def _extract_shortcode_from_url(value: str) -> str:
    text = value.strip()
    for marker in ("/p/", "/reel/", "/tv/"):
        if marker in text:
            tail = text.split(marker, maxsplit=1)[1]
            return _normalize_shortcode(tail.split("/", maxsplit=1)[0])
    return _normalize_shortcode(text)


if __name__ == "__main__":
    raise SystemExit(main())
