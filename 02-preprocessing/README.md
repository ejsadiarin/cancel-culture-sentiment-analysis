# Preprocessing

This module contains the preprocessing pipeline that transforms raw YouTube collection outputs into
flat, analysis-ready tables for sentiment and social network analysis.

All preprocessing reads from the repository-level `data/` directory and writes outputs to
`02-preprocessing/outputs/`.

## Inputs (from repo root `data/`)

Per influencer (e.g., `bodeoum_tv`, `mimiminu`):

- `data/<person>/<person>_youtube.jsonl` (video metadata)
- `data/<person>/comments/*.info.json` (threaded comments)
- `data/<person>/transcripts/*.ko.txt` (transcripts)
- `data/input/<person>.csv` (window map: pre/cancel/post)

## Outputs (written by preprocessing)

Per influencer under `02-preprocessing/outputs/<person>/`:

- `videos.csv` (video metadata + window label)
- `comments.csv` (flattened comments)
- `edges.csv` (reply graph edges)
- `transcripts.csv` (slot/window + transcript text)

## Notebook (single task)

The preprocessing task is captured in a single notebook:

- `02-preprocessing/notebooks/01_preprocessing.ipynb`

This notebook loads raw inputs from `data/`, builds the output tables, and saves them into
`02-preprocessing/outputs/`.

## Module-local uv environment

```bash
uv venv 02-preprocessing/.venv
uv sync --directory 02-preprocessing
uv run --directory 02-preprocessing python -V
```

Keep dependencies for preprocessing in `02-preprocessing/pyproject.toml` so they do not affect other stages.

## CLI

Run the notebook via the module CLI:

```bash
uv run --directory 02-preprocessing preprocessing
```
