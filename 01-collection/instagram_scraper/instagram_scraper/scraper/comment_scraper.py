from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import instaloader

from ..models import CommentItem


class CommentScraper:
    def __init__(self, *, max_comments_per_post: int) -> None:
        self.max_comments_per_post = (
            max_comments_per_post if max_comments_per_post > 0 else 10**9
        )

    def scrape_comments(
        self, account_username: str, post: instaloader.Post
    ) -> list[CommentItem]:
        out: list[CommentItem] = []
        try:
            for idx, comment in enumerate(post.get_comments()):
                if idx >= self.max_comments_per_post:
                    break
                owner = getattr(comment, "owner", None)
                comment_id = str(getattr(comment, "id", "")) or _fallback_comment_id(
                    post.shortcode, idx
                )
                out.append(
                    CommentItem(
                        account_username=account_username,
                        post_shortcode=post.shortcode,
                        comment_id=comment_id,
                        text=(getattr(comment, "text", "") or "").strip(),
                        user_handle=getattr(owner, "username", None),
                        user_display_name=getattr(owner, "full_name", None)
                        or getattr(owner, "username", None),
                        like_count=getattr(comment, "likes_count", None),
                        reply_count=_reply_count(comment),
                        is_reply=False,
                        parent_comment_id=None,
                        reply_to_user_handle=None,
                        create_time=_normalize_dt(
                            getattr(comment, "created_at_utc", None)
                        ),
                        raw={
                            "owner_id": getattr(owner, "userid", None),
                        },
                    )
                )

                for ridx, reply in enumerate(_iter_answers(comment)):
                    reply_owner = getattr(reply, "owner", None)
                    out.append(
                        CommentItem(
                            account_username=account_username,
                            post_shortcode=post.shortcode,
                            comment_id=str(getattr(reply, "id", ""))
                            or _fallback_reply_id(post.shortcode, comment_id, ridx),
                            text=(getattr(reply, "text", "") or "").strip(),
                            user_handle=getattr(reply_owner, "username", None),
                            user_display_name=getattr(reply_owner, "full_name", None)
                            or getattr(reply_owner, "username", None),
                            like_count=getattr(reply, "likes_count", None),
                            reply_count=None,
                            is_reply=True,
                            parent_comment_id=comment_id,
                            reply_to_user_handle=getattr(owner, "username", None),
                            create_time=_normalize_dt(
                                getattr(reply, "created_at_utc", None)
                            ),
                            raw={
                                "owner_id": getattr(reply_owner, "userid", None),
                                "parent_comment_id": comment_id,
                            },
                        )
                    )
        except Exception:  # noqa: BLE001
            out.extend(
                _extract_preview_comments(
                    account_username=account_username,
                    post=post,
                    max_comments=self.max_comments_per_post,
                )
            )

        return _dedupe_nonempty(out)


def _fallback_comment_id(post_shortcode: str, index: int) -> str:
    return f"{post_shortcode}::c::{index}"


def _fallback_reply_id(post_shortcode: str, comment_id: str, index: int) -> str:
    return f"{post_shortcode}::r::{comment_id}::{index}"


def _iter_answers(comment: object):
    answers = getattr(comment, "answers", None)
    if answers is None:
        return []
    try:
        return list(answers)
    except Exception:  # noqa: BLE001
        return []


def _extract_preview_comments(
    *, account_username: str, post: instaloader.Post, max_comments: int
) -> list[CommentItem]:
    node = getattr(post, "_node", None)
    if not isinstance(node, dict):
        return []

    root_edges = _comment_edges_from_node(node)
    out: list[CommentItem] = []

    for idx, edge in enumerate(root_edges):
        if idx >= max_comments:
            break
        comment_node = edge.get("node") if isinstance(edge, dict) else None
        if not isinstance(comment_node, dict):
            continue

        comment_id = str(
            comment_node.get("id") or _fallback_comment_id(post.shortcode, idx)
        )
        owner = (
            comment_node.get("owner")
            if isinstance(comment_node.get("owner"), dict)
            else {}
        )
        owner_username = _as_str(owner.get("username"))

        out.append(
            CommentItem(
                account_username=account_username,
                post_shortcode=post.shortcode,
                comment_id=comment_id,
                text=(_as_str(comment_node.get("text")) or "").strip(),
                user_handle=owner_username,
                user_display_name=_as_str(owner.get("full_name")) or owner_username,
                like_count=_as_int(_nested(comment_node, "edge_liked_by", "count")),
                reply_count=_as_int(
                    _nested(comment_node, "edge_threaded_comments", "count")
                ),
                is_reply=False,
                parent_comment_id=None,
                reply_to_user_handle=None,
                create_time=_from_unix(comment_node.get("created_at")),
                raw={
                    "owner_id": owner.get("id"),
                    "source": "preview_fallback",
                },
            )
        )

        reply_edges = _nested(comment_node, "edge_threaded_comments", "edges")
        if not isinstance(reply_edges, list):
            continue
        for ridx, redge in enumerate(reply_edges):
            reply_node = redge.get("node") if isinstance(redge, dict) else None
            if not isinstance(reply_node, dict):
                continue
            reply_owner = (
                reply_node.get("owner")
                if isinstance(reply_node.get("owner"), dict)
                else {}
            )
            out.append(
                CommentItem(
                    account_username=account_username,
                    post_shortcode=post.shortcode,
                    comment_id=str(
                        reply_node.get("id")
                        or _fallback_reply_id(post.shortcode, comment_id, ridx)
                    ),
                    text=(_as_str(reply_node.get("text")) or "").strip(),
                    user_handle=_as_str(reply_owner.get("username")),
                    user_display_name=_as_str(reply_owner.get("full_name"))
                    or _as_str(reply_owner.get("username")),
                    like_count=_as_int(_nested(reply_node, "edge_liked_by", "count")),
                    reply_count=None,
                    is_reply=True,
                    parent_comment_id=comment_id,
                    reply_to_user_handle=owner_username,
                    create_time=_from_unix(reply_node.get("created_at")),
                    raw={
                        "owner_id": reply_owner.get("id"),
                        "parent_comment_id": comment_id,
                        "source": "preview_fallback",
                    },
                )
            )

    return out


def _comment_edges_from_node(node: dict[str, Any]) -> list[dict[str, Any]]:
    keys = (
        "edge_media_to_parent_comment",
        "edge_media_to_comment",
        "edge_media_preview_comment",
    )
    for key in keys:
        container = node.get(key)
        if not isinstance(container, dict):
            continue
        edges = container.get("edges")
        if isinstance(edges, list) and edges:
            return [e for e in edges if isinstance(e, dict)]
    return []


def _nested(data: dict[str, Any], *path: str) -> Any:
    cur: Any = data
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _from_unix(value: object) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except Exception:  # noqa: BLE001
        return None


def _as_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:  # noqa: BLE001
        return None


def _as_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _dedupe_nonempty(items: list[CommentItem]) -> list[CommentItem]:
    out: list[CommentItem] = []
    seen: set[str] = set()
    for item in items:
        if not item.text:
            continue
        key = item.comment_id.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _reply_count(comment: object) -> int | None:
    answers = getattr(comment, "answers", None)
    if answers is None:
        return None
    try:
        return len(list(answers))
    except Exception:  # noqa: BLE001
        return None


def _normalize_dt(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
