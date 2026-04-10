# TikTok Scraper (Modular)

This module is a standalone TikTok collection pipeline under `01-collection/tiktok_scraper`.
It is intentionally separated so an Instagram scraper can be added later without mixing code.

## What it collects

- Profile/account snapshot metadata
- Video metadata and media links
- Deep comment collection for social network analysis
- Optional speech-to-text transcripts (post-step)
- Publish date filtering (`start-date` to `end-date`)
- JSONL output for analytics pipelines

## Project layout

```text
01-collection/tiktok_scraper/
  README.md
  requirements.txt
  tiktok_scraper/
    cli.py
    models.py
    filters/
      timeframe.py
    scraper/
      session.py
      profile_scraper.py
      video_scraper.py
      comment_scraper.py
      parsing.py
    storage/
      jsonl_writer.py
    transcription/
      whisper_transcriber.py
```

## Install

Use a module-local `uv` environment from repository root:

```bash
uv venv 01-collection/tiktok_scraper/.venv
source 01-collection/tiktok_scraper/.venv/bin/activate
uv sync --directory 01-collection/tiktok_scraper
uv run --directory 01-collection/tiktok_scraper playwright install chromium
```

Alternative (legacy pip flow):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r 01-collection/tiktok_scraper/requirements.txt
python -m playwright install chromium
```

## Quick start

From repository root:

```bash
uv run --directory 01-collection/tiktok_scraper python -m tiktok_scraper.cli \
  --account someuser \
  --start-date 2025-01-01 \
  --end-date 2025-12-31 \
  --out 01-collection/tiktok_scraper/data/tiktok_someuser_2025.jsonl
```

Multiple accounts:

```bash
uv run --directory 01-collection/tiktok_scraper python -m tiktok_scraper.cli \
  --account user1 \
  --account user2 \
  --start-date 2024-01-01 \
  --end-date 2026-01-01 \
  --out 01-collection/tiktok_scraper/data/tiktok_multi.jsonl
```

With heavier crawl settings for network analysis:

```bash
uv run --directory 01-collection/tiktok_scraper python -m tiktok_scraper.cli \
  --account someuser \
  --start-date 2020-01-01 \
  --end-date 2026-12-31 \
  --max-videos 1200 \
  --max-comments-per-video 0 \
  --min-delay 1.2 \
  --max-delay 3.0 \
  --out 01-collection/tiktok_scraper/data/tiktok_deep.jsonl
```

Notes:
- `--max-comments-per-video 0` means no effective cap (collect as many as discovered).
- Very large crawls can take hours and may still be limited by TikTok UI/rate controls.

## CLI options

- `--account` repeatable username flag (without `@` preferred)
- `--start-date` publish date lower bound (`YYYY-MM-DD`)
- `--end-date` publish date upper bound (`YYYY-MM-DD`)
- `--out` output JSONL path
- `--max-videos` max profile videos to process (default `500`)
- `--max-comments-per-video` default `5000`, use `0` for unbounded mode
- `--headless / --no-headless` browser mode (default headless)
- `--cookie-file` Playwright storage state JSON for authenticated sessions
- `--timeout-ms` per-page timeout (default `45000`)
- `--min-delay`, `--max-delay` pacing between actions
- `--transcribe` to run inline transcription per scraped video
- `--transcription-model` faster-whisper model name (default `small`)

## Output format (JSONL)

Each line is one JSON record with `record_type`:

- `account`
- `video`
- `comment`
- `transcript` (if transcription enabled)

Common fields:

- `run_id`
- `scraped_at`
- `source_account`

### Sample `video` record

```json
{
  "record_type": "video",
  "run_id": "f63d9f7f...",
  "scraped_at": "2026-04-10T20:00:00+00:00",
  "source_account": "someuser",
  "video_id": "7460123456789012345",
  "video_url": "https://www.tiktok.com/@someuser/video/7460123456789012345",
  "description": "example caption #topic",
  "create_time": "2025-03-09T10:04:12+00:00",
  "view_count": 20031,
  "like_count": 1302,
  "comment_count": 211,
  "share_count": 73,
  "hashtags": ["topic"],
  "mentions": [],
  "video_play_url": "https://...",
  "cover_url": "https://...",
  "music_url": "https://..."
}
```

## Optional transcription workflow

Current scraper supports inline transcription with `--transcribe`, but recommended workflow is:

1. Run scrape first (metadata/comments/videos).
2. Run a separate transcription pass for reproducibility and easier retries.

You can extend `tiktok_scraper/transcription/whisper_transcriber.py` to consume prior JSONL video records and write transcript-only JSONL.

## Important reliability notes

- TikTok changes frontend structure frequently; selectors may need periodic updates.
- For deep comment crawls, use slower delays to reduce blocking.
- If public pages are restricted, create a logged-in browser session and pass `--cookie-file`.

## Legal and ethical usage

Use this tool responsibly and in compliance with TikTok terms, local law, and your institution's research ethics requirements.
Only collect data you are authorized to collect and store.
