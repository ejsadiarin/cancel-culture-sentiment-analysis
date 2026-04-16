# cancel-culture-sentiment-analysis

Sentiment and network analysis of cancel culture discourse (PH vs KR), organized as a modular pipeline.

## Pipeline modules

- `01-collection`: Data collection stage (`youtube_scraper`)
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

- `01-collection/youtube_scraper`: runs from a manual CSV list of videos (pre/cancel/post).
- `02-preprocessing`: scaffolded with an empty dependency list; add packages to `02-preprocessing/pyproject.toml` as needed.
- `03-analysis`: scaffolded with an empty dependency list; add analysis/modeling dependencies in `03-analysis/pyproject.toml`.
- `04-evaluation`: scaffolded with an empty dependency list; add metrics/reporting dependencies in `04-evaluation/pyproject.toml`.

Process overview:

- YouTube process: manual CSV -> per-video metadata/comments -> JSONL.
- All collectors emit compatible record types (`video`, `comment`) with shared fields (`run_id`, `scraped_at`, `source_account`).
