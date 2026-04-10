# Preprocessing

This module contains data cleaning and transformation steps between collection and analysis.

## Module-local uv environment

```bash
uv venv 02-preprocessing/.venv
uv sync --directory 02-preprocessing
uv run --directory 02-preprocessing python -V
```

Keep dependencies for preprocessing in `02-preprocessing/pyproject.toml` so they do not affect other stages.
