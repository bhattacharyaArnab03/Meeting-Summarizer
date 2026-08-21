import re
from pathlib import Path
from uuid import uuid4

from app.models.schemas import MeetingResult
from app.services.storage_service import StorageService
from app.services.transcription_service import TranscriptionService
from app.services.gemini_service import GeminiService

ALLOWED_AUDIO_TYPES = {
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "video/mp4": ".mp4",
    "application/mp4": ".mp4",
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
}


class MeetingService:
    def __init__(self, storage: StorageService, gemini: GeminiService | None = None):
        self.storage = storage
        self.gemini = gemini

    @staticmethod
    def validate_upload(content: bytes, mime_type: str, max_bytes: int) -> str:
        if not content:
            raise ValueError("The uploaded audio file is empty.")
        if len(content) > max_bytes:
            raise ValueError(f"The audio file exceeds the {max_bytes // 1024 // 1024} MB limit.")
        extension = ALLOWED_AUDIO_TYPES.get(mime_type.lower())
        if extension is None:
            raise ValueError("Unsupported recording type. Use WAV, MP3, M4A, MP4, WebM, or OGG.")
        return extension

    def process(self, filename: str, content: bytes, mime_type: str, max_bytes: int) -> MeetingResult:
        extension = self.validate_upload(content, mime_type, max_bytes)
        if self.gemini is None:
            raise RuntimeError("GEMINI_API_KEY is not configured. Add it to the local .env file.")

        meeting_id = uuid4().hex
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename or "meeting").name)
        audio_path = self.storage.upload_path(meeting_id, extension)
        audio_path.write_bytes(content)
        try:
            transcript = TranscriptionService(self.gemini).transcribe(audio_path, mime_type)
            if not transcript.strip():
                raise RuntimeError("Transcription returned no usable text.")
            summary = self.gemini.summarize(transcript)
            result = MeetingResult(meeting_id=meeting_id, filename=safe_name, transcript=transcript, summary=summary)
            self.storage.save_result(result)
            return result
        finally:
            audio_path.unlink(missing_ok=True)
