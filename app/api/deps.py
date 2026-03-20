"""
NAYAM (नयम्) — API Dependencies.

Provides shared FastAPI dependencies for authentication,
database sessions, and role-based access control.
"""

import logging
import uuid
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token, token_blacklist
from app.models.user import User, UserRole
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the JWT token and return the authenticated user.

    Args:
        token: The Bearer token from the Authorization header.
        db: The database session.

    Returns:
        The authenticated User object.

    Raises:
        HTTPException: 401 if the token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token in token_blacklist:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise credentials_exception

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_uuid)
    if user is None:
        raise credentials_exception

    return user


def require_roles(allowed_roles: List[UserRole]):
    """
    Factory that returns a dependency enforcing role-based access.

    Args:
        allowed_roles: List of UserRole enums permitted to access the endpoint.

    Returns:
        A FastAPI dependency function that validates the user's role.
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """
        Validate that the current user has one of the allowed roles.

        Args:
            current_user: The authenticated user from JWT.

        Returns:
            The user if authorized.

        Raises:
            HTTPException: 403 if the user lacks the required role.
        """
        if current_user.role not in allowed_roles:
            logger.warning(
                "Access denied for user %s with role %s. Required: %s",
                current_user.id,
                current_user.role,
                allowed_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return current_user

    return role_checker
