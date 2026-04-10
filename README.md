# cancel-culture-sentiment-analysis

Sentiment and network analysis of cancel culture discourse (PH vs KR), organized as a modular pipeline.

## Pipeline modules

- `01-collection`: Data collection stage (currently contains `tiktok_scraper`)
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
- `02-preprocessing`
- `03-analysis`
- `04-evaluation`

```bash
uv venv <module-dir>/.venv
uv sync --directory <module-dir>
uv run --directory <module-dir> python -V
```

### Stage-specific notes

- `01-collection/tiktok_scraper`: scraper dependencies are already defined; run `playwright install chromium` via `uv run`.
- `02-preprocessing`: scaffolded with an empty dependency list; add packages to `02-preprocessing/pyproject.toml` as needed.
- `03-analysis`: scaffolded with an empty dependency list; add analysis/modeling dependencies in `03-analysis/pyproject.toml`.
- `04-evaluation`: scaffolded with an empty dependency list; add metrics/reporting dependencies in `04-evaluation/pyproject.toml`.

### Collection quick start

```bash
uv venv 01-collection/tiktok_scraper/.venv
uv sync --directory 01-collection/tiktok_scraper
uv run --directory 01-collection/tiktok_scraper playwright install chromium
uv run --directory 01-collection/tiktok_scraper python -m tiktok_scraper.cli --help
```
