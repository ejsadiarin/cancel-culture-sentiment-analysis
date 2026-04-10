# Analysis

This module contains modeling, sentiment analysis, and network analysis workflows.

## Module-local uv environment

```bash
uv venv 03-analysis/.venv
uv sync --directory 03-analysis
uv run --directory 03-analysis python -V
```

Keep dependencies for analysis in `03-analysis/pyproject.toml` so only this stage installs them.
