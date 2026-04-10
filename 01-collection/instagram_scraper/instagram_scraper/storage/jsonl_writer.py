from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonlWriter:
    def __init__(self, output_path: str) -> None:
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.output_path.open("a", encoding="utf-8")
        self._seen: dict[str, set[str]] = {
            "video": set(),
            "comment": set(),
        }

    def close(self) -> None:
        self._fh.close()

    def write(self, record: dict[str, Any]) -> bool:
        record_type = record.get("record_type")
        key = self._key_for(record)
        if record_type in self._seen and key is not None:
            if key in self._seen[record_type]:
                return False
            self._seen[record_type].add(key)
        self._fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._fh.flush()
        return True

    @staticmethod
    def _key_for(record: dict[str, Any]) -> str | None:
        record_type = record.get("record_type")
        if record_type == "video":
            video_id = record.get("video_id")
            return str(video_id) if video_id is not None else None
        if record_type == "comment":
            video_id = record.get("video_id")
            comment_id = record.get("comment_id")
            if video_id is None or comment_id is None:
                return None
            return f"{video_id}::{comment_id}"
        return None
