import json
import logging
import re
from typing import Any

from google import genai
from google.genai import types

from app.models.schemas import MeetingSummary
from app.prompts.summarization_prompt import build_summary_prompt

logger = logging.getLogger(__name__)


class GeminiServiceError(RuntimeError):
    pass


def parse_summary_response(response: Any) -> MeetingSummary:
    parsed = getattr(response, "parsed", None)
    if parsed is not None:
        return MeetingSummary.model_validate(parsed)

    text = (getattr(response, "text", None) or "").strip()
    if not text:
        raise ValueError("The summarization provider returned no text.")
    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    candidate = fenced_match.group(1) if fenced_match else text
    if not fenced_match and not candidate.startswith("{"):
        object_match = re.search(r"\{.*\}", candidate, re.DOTALL)
        candidate = object_match.group(0) if object_match else candidate
    return MeetingSummary.model_validate(json.loads(candidate))


class GeminiService:
    def __init__(self, api_key: str, model: str, client: Any | None = None):
        if not api_key and client is None:
            raise GeminiServiceError("GEMINI_API_KEY is not configured. Add it to the local .env file.")
        self.model = model
        self.client = client or genai.Client(api_key=api_key)

    def transcribe(self, audio_path: str, mime_type: str) -> str:
        try:
            audio = self.client.files.upload(file=audio_path, config=types.UploadFileConfig(mime_type=mime_type))
            response = self.client.models.generate_content(
                model=self.model,
                contents=[audio, "Transcribe this meeting recording completely. Return only the transcript text."],
            )
            transcript = (response.text or "").strip()
        except Exception as exc:
            logger.exception("Gemini transcription request failed")
            raise GeminiServiceError("Transcription provider request failed.") from exc
        if not transcript:
            raise GeminiServiceError("The transcription provider returned an empty transcript.")
        return transcript

    def summarize(self, transcript: str) -> MeetingSummary:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=build_summary_prompt(transcript),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=MeetingSummary,
                ),
            )
            return parse_summary_response(response)
        except Exception as exc:
            logger.exception("Gemini summary request or validation failed")
            raise GeminiServiceError("The summarization provider returned an invalid response.") from exc
