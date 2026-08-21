import logging
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.config import get_settings
from app.models.schemas import HealthResponse, MeetingResult
from app.services.gemini_service import GeminiService, GeminiServiceError
from app.services.meeting_service import MeetingService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)
router = APIRouter()


def build_meeting_service() -> MeetingService:
    settings = get_settings()
    gemini = GeminiService(settings.gemini_api_key, settings.gemini_model)
    return MeetingService(StorageService(settings.data_dir), gemini)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/api/meetings/process", response_model=MeetingResult)
def process_meeting(file: Annotated[UploadFile, File(...)]) -> MeetingResult:
    settings = get_settings()
    try:
        content = file.file.read(settings.max_upload_bytes + 1)
        MeetingService.validate_upload(content, file.content_type or "", settings.max_upload_bytes)
        service = build_meeting_service()
        return service.process(file.filename or "meeting", content, file.content_type or "", settings.max_upload_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (GeminiServiceError, RuntimeError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected meeting processing failure")
        raise HTTPException(status_code=500, detail="Meeting processing failed unexpectedly.") from exc
