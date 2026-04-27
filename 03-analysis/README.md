# Analysis

This module contains modeling, sentiment analysis, and network analysis workflows.

## Notebooks

- `03-analysis/notebooks/02_social_network_analysis.ipynb` - Social network analysis
- `03-analysis/notebooks/04_sentiment_analysis.ipynb` - Sentiment trajectory analysis

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