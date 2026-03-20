"""
NAYAM (नयम्) — Authentication API Routes.

Provides register and login endpoints.
All business logic is delegated to AuthService.
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Register a new user account.

    Args:
        payload: Registration data.
        db: Database session (injected).

    Returns:
        JWT token and user data.
    """
    service = AuthService(db)
    user, token = service.register(payload)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT token",
)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate and receive a JWT access token.

    Args:
        payload: Login credentials.
        db: Database session (injected).

    Returns:
        JWT token and user data.
    """
    service = AuthService(db)
    user, token = service.login(payload)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )
