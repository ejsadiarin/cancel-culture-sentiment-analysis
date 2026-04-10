from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import requests
from faster_whisper import WhisperModel

from ..models import TranscriptItem


class WhisperTranscriber:
    def __init__(
        self, *, model_name: str = "small", compute_type: str = "int8"
    ) -> None:
        self.model = WhisperModel(model_name, compute_type=compute_type)

    def transcribe_video(
        self,
        *,
        account_username: str,
        video_id: str,
        video_url: str | None,
        language: str | None,
    ) -> TranscriptItem | None:
        if not video_url:
            return None
        with tempfile.TemporaryDirectory(prefix="ttk_audio_") as temp_dir:
            output_path = Path(temp_dir) / f"{video_id}.mp4"
            if not _download_file(video_url, output_path):
                return None
            segments, info = self.model.transcribe(str(output_path), language=language)
            out_segments: list[dict[str, Any]] = []
            merged: list[str] = []
            for segment in segments:
                text = segment.text.strip()
                if text:
                    merged.append(text)
                out_segments.append(
                    {
                        "start": segment.start,
                        "end": segment.end,
                        "text": text,
                    }
                )
            return TranscriptItem(
                account_username=account_username,
                video_id=video_id,
                video_url=video_url,
                language=(info.language if info else language),
                text=" ".join(merged).strip(),
                segments=out_segments,
            )


def _download_file(url: str, output_path: Path) -> bool:
    try:
        response = requests.get(url, timeout=90)
        if response.status_code != 200:
            return False
        output_path.write_bytes(response.content)
        return True
    except requests.RequestException:
        return False
