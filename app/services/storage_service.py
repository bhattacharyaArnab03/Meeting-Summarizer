import json
from pathlib import Path

from app.models.schemas import MeetingResult


class StorageService:
    def __init__(self, data_dir: Path):
        self.uploads_dir = data_dir / "uploads"
        self.transcripts_dir = data_dir / "transcripts"
        self.summaries_dir = data_dir / "summaries"
        for directory in (self.uploads_dir, self.transcripts_dir, self.summaries_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def upload_path(self, meeting_id: str, suffix: str) -> Path:
        return self.uploads_dir / f"{meeting_id}{suffix}"

    def save_result(self, result: MeetingResult) -> None:
        (self.transcripts_dir / f"{result.meeting_id}.txt").write_text(result.transcript, encoding="utf-8")
        (self.summaries_dir / f"{result.meeting_id}.json").write_text(
            json.dumps(result.model_dump(), indent=2), encoding="utf-8"
        )
