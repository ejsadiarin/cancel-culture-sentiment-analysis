# Evaluation

This module contains validation, benchmarking, and result quality checks.

## Module-local uv environment

```bash
uv venv 04-evaluation/.venv
uv sync --directory 04-evaluation
uv run --directory 04-evaluation python -V
```

Keep dependencies for evaluation in `04-evaluation/pyproject.toml` so this stage stays isolated.
