from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class YtDlpClient:
    def __init__(self, *, cache_dir: str | None = None) -> None:
        self.cache_dir = cache_dir

    def dump_json(self, url: str) -> dict[str, Any]:
        args = ["yt-dlp", "--dump-json", "--no-playlist", url]
        if self.cache_dir:
            args.extend(["--cache-dir", self.cache_dir])
        payload = self._run(args)
        return self._parse_json(payload)

    def dump_json_entries(
        self,
        url: str,
        *,
        flat: bool = True,
        playlist_end: int = 200,
    ) -> list[dict[str, Any]]:
        args = [
            "yt-dlp",
            "--dump-json",
            "--playlist-end",
            str(max(1, int(playlist_end))),
        ]
        if flat:
            args.append("--flat-playlist")
        args.append(url)
        if self.cache_dir:
            args.extend(["--cache-dir", self.cache_dir])
        return list(self._iter_json_entries(args))

    def dump_comments(self, url: str, *, output_dir: str) -> Path | None:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        output_template = out_dir / "%(id)s.%(ext)s"
        args = [
            "yt-dlp",
            "--write-comments",
            "--skip-download",
            "--no-playlist",
            "-o",
            str(output_template),
            url,
        ]
        if self.cache_dir:
            args.extend(["--cache-dir", self.cache_dir])
        self._run(args)
        return self._find_comments_file(out_dir)

    @staticmethod
    def _parse_json(payload: str) -> dict[str, Any]:
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _iter_json_entries(args: list[str]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert process.stdout is not None
        assert process.stderr is not None
        for line in process.stdout:
            if not line.strip():
                continue
            items.append(YtDlpClient._parse_json(line))
        stderr = process.stderr.read()
        returncode = process.wait()
        if returncode != 0:
            raise subprocess.CalledProcessError(
                returncode,
                args,
                output="",
                stderr=stderr,
            )
        return items

    @staticmethod
    def _find_comments_file(out_dir: Path) -> Path | None:
        candidates = list(out_dir.glob("*.comments.json"))
        if not candidates:
            candidates = list(out_dir.glob("*.comments.jsonl"))
        if not candidates:
            return None
        return max(candidates, key=lambda p: p.stat().st_mtime)

    @staticmethod
    def _run(args: list[str]) -> str:
        result = subprocess.run(
            args,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
