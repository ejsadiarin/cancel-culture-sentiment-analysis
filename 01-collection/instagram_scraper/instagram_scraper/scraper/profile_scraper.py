from __future__ import annotations

from dataclasses import dataclass

import instaloader

from ..models import AccountSnapshot
from .session import InstagramSession


@dataclass(slots=True)
class ProfileScrapeResult:
    account: AccountSnapshot
    posts: list[instaloader.Post]


class ProfileScraper:
    def __init__(self, session: InstagramSession, *, max_posts: int) -> None:
        self.session = session
        self.max_posts = max_posts

    def scrape(self, username: str) -> ProfileScrapeResult:
        profile = self.session.with_retry(
            lambda: instaloader.Profile.from_username(
                self.session.loader.context, username
            )
        )
        self.session.human_delay()

        account = AccountSnapshot(
            username=username,
            display_name=getattr(profile, "full_name", None),
            biography=getattr(profile, "biography", None),
            followers=getattr(profile, "followers", None),
            following=getattr(profile, "followees", None),
            post_count=getattr(profile, "mediacount", None),
            is_private=getattr(profile, "is_private", None),
            is_verified=getattr(profile, "is_verified", None),
            scrape_url=f"https://www.instagram.com/{username}/",
        )

        posts: list[instaloader.Post] = []
        for post in profile.get_posts():
            posts.append(post)
            if len(posts) >= self.max_posts:
                break
            self.session.human_delay()

        return ProfileScrapeResult(account=account, posts=posts)
