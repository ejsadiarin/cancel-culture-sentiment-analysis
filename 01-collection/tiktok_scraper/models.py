from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class AccountSnapshot:
    username: str
    display_name: str | None = None
    bio: str | None = None
    followers: int | None = None
    following: int | None = None
    likes: int | None = None
    scrape_url: str | None = None

    def to_record(self, *, run_id: str, scraped_at: str) -> dict[str, Any]:
        return {
            "record_type": "account",
            "run_id": run_id,
            "scraped_at": scraped_at,
            "source_account": self.username,
            "username": self.username,
            "display_name": self.display_name,
            "bio": self.bio,
            "followers": self.followers,
            "following": self.following,
            "likes": self.likes,
            "scrape_url": self.scrape_url,
        }


@dataclass(slots=True)
class VideoItem:
    account_username: str
    video_id: str
    video_url: str
    description: str | None = None
    create_time: datetime | None = None
    duration_seconds: int | None = None
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    share_count: int | None = None
    hashtags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    language: str | None = None
    is_pinned: bool | None = None
    video_play_url: str | None = None
    cover_url: str | None = None
    music_url: str | None = None
    music_title: str | None = None
    music_author: str | None = None
    author_display_name: str | None = None
    author_follower_count: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_record(self, *, run_id: str, scraped_at: str) -> dict[str, Any]:
        return {
            "record_type": "video",
            "run_id": run_id,
            "scraped_at": scraped_at,
            "source_account": self.account_username,
            "video_id": self.video_id,
            "video_url": self.video_url,
            "description": self.description,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "duration_seconds": self.duration_seconds,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "share_count": self.share_count,
            "hashtags": self.hashtags,
            "mentions": self.mentions,
            "language": self.language,
            "is_pinned": self.is_pinned,
            "video_play_url": self.video_play_url,
            "cover_url": self.cover_url,
            "music_url": self.music_url,
            "music_title": self.music_title,
            "music_author": self.music_author,
            "author_display_name": self.author_display_name,
            "author_follower_count": self.author_follower_count,
            "raw": self.raw,
        }


@dataclass(slots=True)
class CommentItem:
    account_username: str
    video_id: str
    comment_id: str
    text: str
    user_handle: str | None = None
    user_display_name: str | None = None
    like_count: int | None = None
    reply_count: int | None = None
    create_time: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_record(self, *, run_id: str, scraped_at: str) -> dict[str, Any]:
        return {
            "record_type": "comment",
            "run_id": run_id,
            "scraped_at": scraped_at,
            "source_account": self.account_username,
            "video_id": self.video_id,
            "comment_id": self.comment_id,
            "text": self.text,
            "user_handle": self.user_handle,
            "user_display_name": self.user_display_name,
            "like_count": self.like_count,
            "reply_count": self.reply_count,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "raw": self.raw,
        }


@dataclass(slots=True)
class TranscriptItem:
    account_username: str
    video_id: str
    video_url: str | None
    language: str | None
    text: str
    segments: list[dict[str, Any]] = field(default_factory=list)

    def to_record(self, *, run_id: str, scraped_at: str) -> dict[str, Any]:
        return {
            "record_type": "transcript",
            "run_id": run_id,
            "scraped_at": scraped_at,
            "source_account": self.account_username,
            "video_id": self.video_id,
            "video_url": self.video_url,
            "language": self.language,
            "text": self.text,
            "segments": self.segments,
        }
