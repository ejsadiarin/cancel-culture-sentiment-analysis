# cancel-culture-sentiment-analysis

Sentiment (emotion) trajectory and social network analysis of cancel culture discourse on YouTube, organized as a modular pipeline.

Current dataset focus: South Korea (KR) longitudinal cases with `pre` / `cancel` / `post` windows (e.g., `data/bodeoum_tv`, `data/mimiminu`).

## Interactive site

The `web/` directory contains a static React walkthrough of the full pipeline, built from the repository's generated CSVs and raw examples. It covers collection, preprocessing, sentiment, network structure, and evaluation, with an interactive case switch for Bodeoum TV and Mimiminu.

```bash
cd web
npm install
npm run dev
```

See [`web/README.md`](web/README.md) for the data generator, production build, Docker, and Vercel instructions.

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

Planned/optional additions:

- Transcripts: download YouTube auto-captions (or temporary audio) and generate text transcripts (e.g., Whisper). Store only transcript text outputs in-repo; keep raw audio/video out of git.

### YouTube CSV example

Create a CSV like `data/input/mimiminu.csv` (or `data/input/bodeoum_tv.csv`):

```text
window,video
pre,https://www.youtube.com/watch?v=J6Kp5l2xF5E
pre,5LmBWb8zWfI
cancel,https://www.youtube.com/watch?v=6UeLUY3h3s0
post,8T7J6f0WzH8
post,https://www.youtube.com/watch?v=4tBnF46ybZk
```

Run:

```bash
uv run --directory 01-collection/youtube_scraper python -m youtube_scraper.cli \
  --manual-csv data/input/gdragon.csv
```

Outputs:

- `data/gdragon/gdragon_youtube.jsonl`
- `data/gdragon/comments/`

Existing examples in this repo:

- `data/bodeoum_tv/` (metadata JSONL + per-video comment `.info.json` files)
- `data/mimiminu/` (metadata JSONL + per-video comment `.info.json` files)
