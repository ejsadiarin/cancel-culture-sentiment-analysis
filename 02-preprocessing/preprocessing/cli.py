from __future__ import annotations

import argparse
import logging
import runpy
import sys
from pathlib import Path

LOGGER = logging.getLogger("preprocessing")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the preprocessing notebook via nbconvert"
    )
    parser.add_argument(
        "--notebook",
        default="02-preprocessing/notebooks/01_preprocessing.ipynb",
        help="Notebook path (repo-root relative or absolute)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (default: INFO)",
    )
    return parser.parse_args(argv)


def _resolve_under_root(path_value: str) -> Path:
    candidate = Path(path_value).expanduser()
    if candidate.is_absolute():
        return candidate
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / candidate


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    notebook_path = _resolve_under_root(str(args.notebook))
    if not notebook_path.exists():
        raise FileNotFoundError(f"Notebook not found: {notebook_path}")

    try:
        import nbconvert  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "nbconvert is required. Install with: uv pip install nbconvert"
        ) from exc

    LOGGER.info("Running notebook: %s", notebook_path)
    sys.argv = [
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        "--inplace",
        str(notebook_path),
    ]
    runpy.run_module("jupyter", run_name="__main__")
    LOGGER.info("Notebook execution complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
