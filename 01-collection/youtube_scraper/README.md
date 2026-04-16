# YouTube Scraper (Modular)

This module is a standalone YouTube collection pipeline under `01-collection/youtube_scraper`.
It is designed to mirror the TikTok/Instagram JSONL output shape so downstream preprocessing
and analysis can share logic.

## What it collects

- Channel/account snapshot metadata
- Anchor apology video metadata
- Pre/cancel/post window video metadata
- Deep comment collection per video (via `yt-dlp --write-comments`)
- JSONL output for analytics pipelines

## Defaults (confirmed)

- Pre window: 30 days before anchor (exclusive of anchor day)
- Cancel window: anchor day through +7 days
- Post window: +8 days through +30 days
- Max videos per window: 50
- Max comments per video: 1000
- Output: single JSONL per anchor run

## Project layout

```text
01-collection/youtube_scraper/
  README.md
  pyproject.toml
  youtube_scraper/
    cli.py
    models.py
    filters/
      timeframe.py
    scraper/
      yt_dlp_client.py
      channel_scraper.py
      video_scraper.py
      comment_scraper.py
    storage/
      jsonl_writer.py
```

## Install (module-local uv)

From repository root:

```bash
uv venv 01-collection/youtube_scraper/.venv
uv sync --directory 01-collection/youtube_scraper
uv run --directory 01-collection/youtube_scraper python -m youtube_scraper.cli --help
```

## Quick start

From repository root:

```bash
uv run --directory 01-collection/youtube_scraper python -m youtube_scraper.cli \
  --anchor-url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --out data/raw/youtube_anchor.jsonl
```

## CLI options

- `--anchor-url` YouTube video URL used as the apology anchor
- `--out` output JSONL path (default `data/raw/youtube_anchor.jsonl`)
- `--pre-days` days before anchor (default `30`)
- `--cancel-days` days after anchor to treat as cancel window (default `7`)
- `--post-days` days after cancel window (default `30`)
- `--max-videos-per-window` default `50`
- `--max-comments-per-video` default `1000`, use `0` for unbounded mode
- `--comments-dir` directory to store comment dump files (default `data/raw/youtube_comments`)
- `--cache-dir` optional `yt-dlp` cache directory

## Output format (JSONL)

Each line is one JSON record with `record_type`:

- `account`
- `video`
- `comment`
- `transcript` (reserved for future use)

Common fields:

- `platform` (`youtube`)
- `run_id`
- `scraped_at`
- `source_account`

Additional window fields:

- `window_label` (`pre`, `cancel`, `post`)
- `anchor_id` (video id of the apology anchor)

## Notes and reliability

- Comment availability depends on `yt-dlp` support for the target video; if comments are
  restricted or unavailable, the scraper will still emit video metadata and continue.
- For large crawls, expect longer runtimes and occasional partial comment dumps.
- Language filtering (PH English and Korean) is recommended in preprocessing rather than
  collection to avoid losing data due to detection noise.

## Legal and ethical usage

Use this tool responsibly and in compliance with YouTube terms, local law, and your
institution's research ethics requirements. Only collect data you are authorized to
collect and store.
