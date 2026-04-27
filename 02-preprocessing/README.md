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

## Notebook

The preprocessing task is captured in a single notebook:

- `02-preprocessing/notebooks/01_preprocessing.ipynb`

This notebook loads raw inputs from `data/`, builds the output tables, and saves them into
`02-preprocessing/outputs/`.

## Environment

This project uses a central venv at the repository root.

### First-time setup

```bash
# Create venv and install dependencies
uv venv
uv sync

# Register Jupyter kernel
.venv/bin/python -m ipykernel install --user --name="cancel-culture" --display-name="Cancel Culture"
```

### Running notebooks

```bash
jupyter notebook
```

Select "Cancel Culture" kernel in Jupyter.

### CLI usage

```bash
uv run python -m preprocessing
```