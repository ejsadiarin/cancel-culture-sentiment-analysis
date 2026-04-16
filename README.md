# cancel-culture-sentiment-analysis

Sentiment and network analysis of cancel culture discourse (PH vs KR), organized as a modular pipeline.

## Pipeline modules

- `01-collection`: Data collection stage (`tiktok_scraper`, `instagram_scraper`)
- `02-preprocessing`: Data cleaning, normalization, and feature preparation
- `03-analysis`: Sentiment, network, and modeling workflows
- `04-evaluation`: Validation, benchmarking, and quality checks

Each module is intentionally isolated so dependencies stay local to that stage.

## uv setup (per module)

This repository uses **one uv environment per module**. This avoids downloading and installing dependencies for stages you are not using.

### Why per-module uv

- Faster setup when working on a single stage
- Smaller environments with fewer dependency conflicts
- Better reproducibility through module-level `uv.lock` files

### Standard workflow for any module

Replace `<module-dir>` with one of:

- `01-collection/tiktok_scraper`
- `01-collection/instagram_scraper`
- `01-collection/youtube_scraper`
- `02-preprocessing`
- `03-analysis`
- `04-evaluation`

```bash
uv venv <module-dir>/.venv
uv sync --directory <module-dir>
uv run --directory <module-dir> python -V
```

### Stage-specific notes

- `01-collection/tiktok_scraper`: browser automation scraper via Playwright; run `playwright install chromium` via `uv run`.
- `01-collection/instagram_scraper`: Instaloader-based scraper, auth-first via reusable session file for better reliability.
- `02-preprocessing`: scaffolded with an empty dependency list; add packages to `02-preprocessing/pyproject.toml` as needed.
- `03-analysis`: scaffolded with an empty dependency list; add analysis/modeling dependencies in `03-analysis/pyproject.toml`.
- `04-evaluation`: scaffolded with an empty dependency list; add metrics/reporting dependencies in `04-evaluation/pyproject.toml`.

### Collection quick start (TikTok)

```bash
uv venv 01-collection/tiktok_scraper/.venv
uv sync --directory 01-collection/tiktok_scraper
uv run --directory 01-collection/tiktok_scraper playwright install chromium
uv run --directory 01-collection/tiktok_scraper python -m tiktok_scraper.cli --help
```

### Collection quick start (Instagram)

Install and verify CLI:

```bash
uv venv 01-collection/instagram_scraper/.venv
uv sync --directory 01-collection/instagram_scraper
uv run --directory 01-collection/instagram_scraper python -m instagram_scraper.cli --help
```

Create/refresh authenticated session (recommended):

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

Run scraper with session auth:

```bash
uv run --directory 01-collection/instagram_scraper python -m instagram_scraper.cli \
  --account somecreator \
  --start-date 2025-01-01 \
  --end-date 2025-12-31 \
  --session-user your_ig_username \
  --session-file 01-collection/instagram_scraper/.ig_session \
  --out data/raw/instagram_somecreator_2025.jsonl
```

Process overview:

- TikTok process: profile scrape -> discover video URLs -> per-video metadata/comments -> optional transcript -> JSONL.
- Instagram process: auth/session load -> profile scrape -> post iteration/date filter -> per-post comments -> JSONL.
- YouTube process: anchor video -> channel uploads -> pre/cancel/post windows -> per-video metadata/comments -> JSONL.
- All collectors emit compatible record types (`account`, `video`, `comment`) with shared fields (`run_id`, `scraped_at`, `source_account`).
