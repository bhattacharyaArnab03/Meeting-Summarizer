from pathlib import Path

from app.services.gemini_service import GeminiService


class TranscriptionService:
    def __init__(self, gemini: GeminiService):
        self.gemini = gemini

    def transcribe(self, audio_path: Path, mime_type: str) -> str:
        return self.gemini.transcribe(str(audio_path), mime_type)
