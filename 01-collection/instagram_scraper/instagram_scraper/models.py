from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class AccountSnapshot:
    username: str
    display_name: str | None = None
    biography: str | None = None
    followers: int | None = None
    following: int | None = None
    post_count: int | None = None
    is_private: bool | None = None
    is_verified: bool | None = None
    scrape_url: str | None = None

    def to_record(self, *, run_id: str, scraped_at: str) -> dict[str, Any]:
        return {
            "platform": "instagram",
            "record_type": "account",
            "run_id": run_id,
            "scraped_at": scraped_at,
            "source_account": self.username,
            "username": self.username,
            "display_name": self.display_name,
            "biography": self.biography,
            "followers": self.followers,
            "following": self.following,
            "post_count": self.post_count,
            "is_private": self.is_private,
            "is_verified": self.is_verified,
            "scrape_url": self.scrape_url,
        }


@dataclass(slots=True)
class PostItem:
    account_username: str
    post_shortcode: str
    post_url: str
    create_time: datetime | None = None
    caption: str | None = None
    like_count: int | None = None
    comment_count: int | None = None
    view_count: int | None = None
    is_video: bool | None = None
    media_type: str | None = None
    hashtags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_record(self, *, run_id: str, scraped_at: str) -> dict[str, Any]:
        return {
            "platform": "instagram",
            "record_type": "video",
            "run_id": run_id,
            "scraped_at": scraped_at,
            "source_account": self.account_username,
            "video_id": self.post_shortcode,
            "video_url": self.post_url,
            "post_shortcode": self.post_shortcode,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "description": self.caption,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "view_count": self.view_count,
            "is_video": self.is_video,
            "media_type": self.media_type,
            "hashtags": self.hashtags,
            "mentions": self.mentions,
            "raw": self.raw,
        }


@dataclass(slots=True)
class CommentItem:
    account_username: str
    post_shortcode: str
    comment_id: str
    text: str
    user_handle: str | None = None
    user_display_name: str | None = None
    like_count: int | None = None
    reply_count: int | None = None
    is_reply: bool = False
    parent_comment_id: str | None = None
    reply_to_user_handle: str | None = None
    create_time: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_record(self, *, run_id: str, scraped_at: str) -> dict[str, Any]:
        return {
            "platform": "instagram",
            "record_type": "comment",
            "run_id": run_id,
            "scraped_at": scraped_at,
            "source_account": self.account_username,
            "video_id": self.post_shortcode,
            "comment_id": self.comment_id,
            "text": self.text,
            "user_handle": self.user_handle,
            "user_display_name": self.user_display_name,
            "like_count": self.like_count,
            "reply_count": self.reply_count,
            "is_reply": self.is_reply,
            "parent_comment_id": self.parent_comment_id,
            "reply_to_user_handle": self.reply_to_user_handle,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "raw": self.raw,
        }
