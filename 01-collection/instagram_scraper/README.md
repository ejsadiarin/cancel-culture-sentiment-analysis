# Instagram Scraper (Modular)

This module is a standalone Instagram collection pipeline under `01-collection/instagram_scraper`.
It is designed to mirror the TikTok JSONL output shape so downstream preprocessing and analysis can share logic.

## What it collects

- Profile/account snapshot metadata
- Post metadata (posts and reels)
- Deep comment collection per post
- Date range filtering (`start-date` to `end-date`)
- JSONL output for analytics pipelines

## Why auth-first

To reduce blocks and improve reliability, this scraper is authentication-first:

- Reuses an Instagram session file when available
- Can log in once and persist session for future runs
- Uses conservative delays and retries with backoff

Anonymous mode is supported only if you explicitly pass `--allow-anonymous`.

## Project layout

```text
01-collection/instagram_scraper/
  README.md
  pyproject.toml
  uv.lock
  instagram_scraper/
    cli.py
    models.py
    filters/
      timeframe.py
    scraper/
      session.py
      profile_scraper.py
      post_scraper.py
      comment_scraper.py
      parsing.py
    storage/
      jsonl_writer.py
```

## Install (module-local uv)

From repository root:

```bash
uv venv 01-collection/instagram_scraper/.venv
uv sync --directory 01-collection/instagram_scraper
uv run --directory 01-collection/instagram_scraper python -m instagram_scraper.cli --help
```

## Authentication setup (recommended)

Create a reusable session file by logging in once:

```bash
export INSTAGRAM_PASSWORD='your_password_here'

uv run --directory 01-collection/instagram_scraper python -m instagram_scraper.cli \
  --account instagram \
  --start-date 2025-01-01 \
  --end-date 2025-01-01 \
  --max-posts 1 \
  --max-comments-per-post 1 \
  --login-user your_ig_username \
  --session-user your_ig_username \
  --session-file 01-collection/instagram_scraper/.ig_session \
  --out data/raw/instagram_session_warmup.jsonl
```

After that, future runs only need:

```bash
--session-user your_ig_username --session-file 01-collection/instagram_scraper/.ig_session
```

## Quick start

From repository root:

```bash
uv run --directory 01-collection/instagram_scraper python -m instagram_scraper.cli \
  --account somecreator \
  --start-date 2025-01-01 \
  --end-date 2025-12-31 \
  --session-user your_ig_username \
  --session-file 01-collection/instagram_scraper/.ig_session \
  --out data/raw/instagram_somecreator_2025.jsonl
```

Multiple accounts:

```bash
uv run --directory 01-collection/instagram_scraper python -m instagram_scraper.cli \
  --account user1 \
  --account user2 \
  --start-date 2024-01-01 \
  --end-date 2026-01-01 \
  --session-user your_ig_username \
  --session-file 01-collection/instagram_scraper/.ig_session \
  --out data/raw/instagram_multi.jsonl
```

Deeper crawl with safer pacing:

```bash
uv run --directory 01-collection/instagram_scraper python -m instagram_scraper.cli \
  --account somecreator \
  --start-date 2020-01-01 \
  --end-date 2026-12-31 \
  --max-posts 1200 \
  --max-comments-per-post 0 \
  --min-delay 1.8 \
  --max-delay 4.2 \
  --max-retries 5 \
  --session-user your_ig_username \
  --session-file 01-collection/instagram_scraper/.ig_session \
  --out data/raw/instagram_deep.jsonl
```

Notes:

- `--max-comments-per-post 0` means unbounded mode.
- For large crawls, increase delay and run fewer accounts per session.

## CLI options

- `--account` repeatable username flag
- `--start-date` lower publish date bound (`YYYY-MM-DD`)
- `--end-date` upper publish date bound (`YYYY-MM-DD`)
- `--out` output JSONL path (default `data/raw/instagram_scrape.jsonl`)
- `--max-posts` max posts to inspect per account (default `400`)
- `--max-comments-per-post` max comments per post (default `3000`, `0` = unbounded)
- `--session-file` path to persistent session file
- `--session-user` Instagram username that owns the session file
- `--login-user` login username used to create/refresh session file
- `--login-password-env` env var containing login password (default `INSTAGRAM_PASSWORD`)
- `--allow-anonymous` run without login/session (less reliable)
- `--min-delay`, `--max-delay` pacing between requests
- `--max-retries` transient failure retries with backoff

## Output format (JSONL)

Each line is one JSON record with `record_type`:

- `account`
- `video` (used for post/reel records to match TikTok-compatible schema)
- `comment`

Common fields:

- `platform` (`instagram`)
- `run_id`
- `scraped_at`
- `source_account`

## Anti-block practices

- Always prefer authenticated sessions (`--session-user`, `--session-file`)
- Keep delays conservative for deep crawls
- Avoid scraping too many accounts in one uninterrupted run
- If rate-limited, pause and resume later using the same session file

## Legal and ethical usage

Use this tool responsibly and in compliance with Instagram terms, local law, and your institution's research ethics requirements.
Only collect data you are authorized to collect and store.
