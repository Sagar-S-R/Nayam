"""
NAYAM (नयम्) — Speech-to-Text API Routes.

Endpoints for audio transcription, content classification,
and intelligent ingestion routing.

Three endpoints:
  POST /transcribe       — Audio → Text (transcription only)
  POST /classify         — Audio → Text → Classify (no entity creation)
  POST /ingest           — Audio → Text → Classify → Route → Create Entity → RAG
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.stt import (
    TranscribeResponse,
    TranscribeAndClassifyResponse,
    TranscribeAndIngestResponse,
    MeetingModeResponse,
)
from app.services.stt import STTService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/transcribe",
    response_model=TranscribeResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe audio to text",
)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file (.wav, .mp3, .m4a, .ogg, .webm, .flac, .aac)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TranscribeResponse:
    """
    Transcribe an audio file to text using Groq Whisper or OpenAI Whisper.

    Supports: .wav, .mp3, .m4a, .ogg, .webm, .flac, .aac, .mp4
    Max file size: 25 MB

    Returns the transcript text, detected language, and audio duration.
    """
    service = STTService(db)
    result = await service.transcribe_only(file)
    return TranscribeResponse(**result)


@router.post(
    "/classify",
    response_model=TranscribeAndClassifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe and classify audio content",
)
async def transcribe_and_classify(
    file: UploadFile = File(..., description="Audio file to transcribe and classify"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TranscribeAndClassifyResponse:
    """
    Transcribe audio and classify the content into one of 5 categories:

    - **policy_document** — Policy drafts, circulars, guidelines, SOPs
    - **citizen_issue** — Complaints, grievances, service requests
    - **meeting_minutes** — Meeting transcripts, discussions
    - **field_report** — Inspection reports, site visit notes
    - **general_query** — Questions for the AI advisor

    No entity is created — use `/ingest` for that.
    """
    service = STTService(db)
    result = await service.transcribe_and_classify(file)
    return TranscribeAndClassifyResponse(**result)


@router.post(
    "/ingest",
    response_model=TranscribeAndIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Transcribe, classify, and ingest audio content",
)
async def transcribe_and_ingest(
    file: UploadFile = File(..., description="Audio file to transcribe and ingest"),
    session_id: Optional[str] = Form(None, description="Agent session ID (for general queries)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> TranscribeAndIngestResponse:
    """
    Full STT pipeline: Audio → Transcribe → Classify → Route → Create Entity → RAG Index.

    This is the "smart ingest" endpoint. It listens to what was said and
    automatically decides what to do with it:

    | Classification     | Action                                 |
    |--------------------|-----------------------------------------|
    | policy_document    | Creates a **Document** record           |
    | citizen_issue      | Creates an **Issue** record             |
    | meeting_minutes    | Creates a **Document** record           |
    | field_report       | Creates a **Document** record           |
    | general_query      | Routes to **AI Agent** (no record)      |

    All transcripts are also chunked and stored as RAG embeddings
    (source_type = "voice_transcript") so the AI agents can reference them.

    Requires: Leader or Staff role.
    """
    service = STTService(db)
    result = await service.transcribe_and_ingest(
        file=file,
        user_id=current_user.id,
        session_id=session_id,
    )
    return TranscribeAndIngestResponse(**result)


@router.post(
    "/meeting-mode",
    response_model=MeetingModeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Meeting Mode: Audio to MoM & Actions",
)
async def meeting_mode(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MeetingModeResponse:
    from app.services.meeting_service import process_meeting_audio
    
    # Optional size limits are now handled by main.py middleware, but we can double check:
    content = await file.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 25MB limit",
        )
    # Reset cursor
    await file.seek(0)
    
    try:
        result = await process_meeting_audio(file, db, str(current_user.id))
        return MeetingModeResponse(**result)
    except Exception as e:
        logger.error(f"Meeting mode failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Meeting Mode processing failed: {str(e)}"
        )
