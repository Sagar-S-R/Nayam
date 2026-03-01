"""
NAYAM (नयम्) — Documents API Routes.

Endpoints for secure document upload, retrieval, and management.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentListResponse,
)
from app.schemas.user import MessageResponse
from app.services.document import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
)
async def upload_document(
    title: str = Form(..., min_length=2, max_length=500, description="Document title"),
    file: UploadFile = File(..., description="The file to upload"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> DocumentUploadResponse:
    """
    Upload a document with secure validation and stub text extraction.

    Requires: Leader or Staff role.
    """
    service = DocumentService(db)
    document = await service.upload_document(
        title=title,
        file=file,
        uploaded_by=current_user.id,
    )
    return DocumentUploadResponse.model_validate(document)


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="List all documents",
)
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentListResponse:
    """
    List documents with pagination.

    Requires: Any authenticated user.
    """
    service = DocumentService(db)
    documents, total = service.list_documents(skip=skip, limit=limit)
    return DocumentListResponse(
        total=total,
        documents=[DocumentUploadResponse.model_validate(d) for d in documents],
    )


@router.get(
    "/{document_id}",
    response_model=DocumentUploadResponse,
    summary="Get document by ID",
)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentUploadResponse:
    """
    Retrieve a single document by UUID.

    Requires: Any authenticated user.
    """
    service = DocumentService(db)
    document = service.get_document(document_id)
    return DocumentUploadResponse.model_validate(document)


@router.delete(
    "/{document_id}",
    response_model=MessageResponse,
    summary="Delete document",
)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER])),
) -> MessageResponse:
    """
    Delete a document and its physical file.

    Requires: Leader role only.
    """
    service = DocumentService(db)
    service.delete_document(document_id)
    return MessageResponse(message="Document deleted successfully.")
