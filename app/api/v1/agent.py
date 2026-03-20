"""
NAYAM (नयम्) — Agent API Routes (Phase 2).

Endpoints for multi-agent conversational queries, session history,
and agent discovery.  All business logic is delegated to AgentService.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.agent import (
    AgentQueryRequest,
    AgentQueryResponse,
    AgentListResponse,
    AgentInfo,
    SessionHistoryResponse,
    SessionHistoryMessage,
)
from app.services.agent import AgentService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/query",
    response_model=AgentQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a query to the NAYAM agent system",
)
def agent_query(
    payload: AgentQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentQueryResponse:
    service = AgentService(db)
    
    # Bhashini Translation Wrapper
    source_lang = payload.metadata.get("language", "en") if payload.metadata else "en"
    
    original_query = payload.query
    if source_lang != "en":
        try:
            from app.services.bhashini import translate_text
            # Translate to English for the LLM
            logger.info(f"Translating query from {source_lang} to English")
            trans_res = translate_text(payload.query, source_lang, "en")
            payload.query = trans_res.get("translated_text", payload.query)
        except Exception as e:
            logger.error(f"Bhashini translation failed before agent: {e}")
            
    result = service.process_query(
        user_id=current_user.id,
        query=payload.query,
        session_id=payload.session_id,
        agent_name=payload.agent_name,
        metadata=payload.metadata,
    )
    
    # Translate back if needed
    if source_lang != "en" and result.get("response"):
        try:
            from app.services.bhashini import translate_text
            logger.info(f"Translating response from English to {source_lang}")
            trans_res = translate_text(result["response"], "en", source_lang)
            result["response"] = trans_res.get("translated_text", result["response"])
        except Exception as e:
            logger.error(f"Bhashini translation failed after agent: {e}")

    return AgentQueryResponse(**result)


@router.get(
    "/agents",
    response_model=AgentListResponse,
    summary="List all available agents",
)
def list_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentListResponse:
    """
    Return the set of registered agents with their descriptions.

    Requires: Any authenticated user.
    """
    service = AgentService(db)
    agents = service.get_available_agents()
    return AgentListResponse(
        agents=[AgentInfo(**a) for a in agents],
    )


@router.get(
    "/sessions/{session_id}/history",
    response_model=SessionHistoryResponse,
    summary="Get conversation history for a session",
)
def get_session_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=200, description="Max messages to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionHistoryResponse:
    """
    Retrieve the ordered conversation messages for a given session.

    Requires: Any authenticated user.
    """
    service = AgentService(db)
    history = service.get_session_history(session_id, limit=limit)
    return SessionHistoryResponse(
        session_id=session_id,
        total=len(history),
        messages=[SessionHistoryMessage(**m) for m in history],
    )
