# Evaluation

This module contains validation, benchmarking, and result quality checks.

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