from __future__ import annotations

import re
from datetime import datetime, timezone

import instaloader

from ..models import PostItem


class PostScraper:
    def to_post_item(self, account_username: str, post: instaloader.Post) -> PostItem:
        caption = (post.caption or "").strip() or None
        hashtags = re.findall(r"#(\w+)", caption or "")
        mentions = re.findall(r"@(\w+)", caption or "")
        created_at = _normalize_dt(getattr(post, "date_utc", None))

        return PostItem(
            account_username=account_username,
            post_shortcode=post.shortcode,
            post_url=f"https://www.instagram.com/p/{post.shortcode}/",
            create_time=created_at,
            caption=caption,
            like_count=getattr(post, "likes", None),
            comment_count=getattr(post, "comments", None),
            view_count=getattr(post, "video_view_count", None),
            is_video=getattr(post, "is_video", None),
            media_type=getattr(post, "typename", None),
            hashtags=hashtags,
            mentions=mentions,
            raw={
                "owner_username": getattr(post.owner_profile, "username", None)
                if getattr(post, "owner_profile", None)
                else None,
                "url": getattr(post, "url", None),
            },
        )


def _normalize_dt(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
