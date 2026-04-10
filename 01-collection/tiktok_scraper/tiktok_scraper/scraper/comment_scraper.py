from __future__ import annotations

import hashlib
import json
from typing import Any

from playwright.sync_api import Page

from ..models import CommentItem
from .parsing import coerce_int, parse_timestamp
from .session import TikTokSession


class CommentScraper:
    def __init__(self, session: TikTokSession, *, max_comments_per_video: int) -> None:
        self.session = session
        self.max_comments_per_video = (
            max_comments_per_video if max_comments_per_video > 0 else 10**9
        )

    def scrape_comments(
        self, account_username: str, video_url: str, video_id: str
    ) -> list[CommentItem]:
        page = self.session.new_page()
        self.session.with_retry(
            lambda: page.goto(video_url, wait_until="domcontentloaded")
        )
        page.wait_for_timeout(2400)
        self.session.human_delay()

        comments = self._collect_from_json(
            payload=self._extract_sigistate_json(page),
            account_username=account_username,
            video_id=video_id,
        )

        if len(comments) < self.max_comments_per_video:
            comments.extend(
                self._collect_from_dom(
                    page=page,
                    account_username=account_username,
                    video_id=video_id,
                    existing_ids={c.comment_id for c in comments},
                )
            )

        page.close()
        return comments[: self.max_comments_per_video]

    def _extract_sigistate_json(self, page: Page) -> dict[str, Any]:
        script = page.locator("#SIGI_STATE")
        if script.count() == 0:
            return {}
        raw_json = script.first.inner_text()
        if not raw_json:
            return {}
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError:
            return {}

    def _collect_from_json(
        self, *, payload: dict[str, Any], account_username: str, video_id: str
    ) -> list[CommentItem]:
        comments: list[CommentItem] = []
        comment_module = payload.get("CommentModule", {})
        if not isinstance(comment_module, dict):
            return comments
        for comment_id, body in comment_module.items():
            if not isinstance(body, dict):
                continue
            text = str(body.get("text", "")).strip()
            if not text:
                continue
            comments.append(
                CommentItem(
                    account_username=account_username,
                    video_id=video_id,
                    comment_id=str(comment_id),
                    text=text,
                    user_handle=body.get("userUniqueId"),
                    user_display_name=body.get("nickname"),
                    like_count=coerce_int(body.get("diggCount")),
                    reply_count=coerce_int(body.get("replyCommentTotal")),
                    create_time=parse_timestamp(body.get("createTime")),
                    raw=body,
                )
            )
            if len(comments) >= self.max_comments_per_video:
                break
        return comments

    def _collect_from_dom(
        self,
        *,
        page: Page,
        account_username: str,
        video_id: str,
        existing_ids: set[str],
    ) -> list[CommentItem]:
        comments: list[CommentItem] = []
        seen = set(existing_ids)
        stable_rounds = 0

        for _ in range(300):
            extracted: list[dict[str, Any]] = page.evaluate(
                """
                () => {
                    const nodes = Array.from(document.querySelectorAll("[data-e2e='comment-item']"));
                    return nodes.map((node) => {
                        const txt = node.querySelector("[data-e2e='comment-level-1']")?.textContent?.trim() ?? "";
                        const user = node.querySelector("a[href*='@']")?.textContent?.trim() ?? null;
                        const likes = node.querySelector("[data-e2e='comment-like-count']")?.textContent?.trim() ?? null;
                        const id = node.getAttribute("id") || node.getAttribute("data-comment-id") || null;
                        return { text: txt, user, likes, id };
                    });
                }
                """
            )
            prev_count = len(comments)
            for raw in extracted:
                text = str(raw.get("text", "")).strip()
                if not text:
                    continue
                comment_id = str(
                    raw.get("id")
                    or _stable_comment_hash(
                        video_id=video_id, text=text, user=raw.get("user")
                    )
                )
                if comment_id in seen:
                    continue
                seen.add(comment_id)
                comments.append(
                    CommentItem(
                        account_username=account_username,
                        video_id=video_id,
                        comment_id=comment_id,
                        text=text,
                        user_handle=raw.get("user"),
                        user_display_name=raw.get("user"),
                        like_count=coerce_int(raw.get("likes")),
                        reply_count=None,
                        create_time=None,
                        raw=raw,
                    )
                )
                if len(comments) >= self.max_comments_per_video:
                    return comments

            if len(comments) == prev_count:
                stable_rounds += 1
            else:
                stable_rounds = 0
            if stable_rounds >= 10:
                break

            page.mouse.wheel(0, 7000)
            page.wait_for_timeout(1300)
            self.session.human_delay()

        return comments


def _stable_comment_hash(*, video_id: str, text: str, user: object) -> str:
    data = f"{video_id}::{user or ''}::{text}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:24]
