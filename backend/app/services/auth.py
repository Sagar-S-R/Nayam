"""
NAYAM (नयम्) — Authentication Service.

Handles registration and login business logic.
No direct DB calls — delegates to UserRepository.
"""

import logging
from typing import Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserRegisterRequest, UserLoginRequest

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service layer for authentication operations.

    Args:
        db: SQLAlchemy database session.
    """

    def __init__(self, db: Session) -> None:
        self.repo = UserRepository(db)

    def register(self, payload: UserRegisterRequest) -> Tuple[User, str]:
        """
        Register a new user.

        Args:
            payload: Registration data including name, email, password, role.

        Returns:
            Tuple of (created User, JWT access token).

        Raises:
            HTTPException: 409 if email is already registered.
        """
        if self.repo.email_exists(payload.email):
            logger.warning("Registration attempt with existing email: %s", payload.email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered.",
            )

        user = User(
            name=payload.name,
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        user = self.repo.create(user)

        token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
        logger.info("User registered successfully: %s", user.email)
        return user, token

    def login(self, payload: UserLoginRequest) -> Tuple[User, str]:
        """
        Authenticate a user and issue a JWT token.

        Args:
            payload: Login data including email and password.

        Returns:
            Tuple of (authenticated User, JWT access token).

        Raises:
            HTTPException: 401 if credentials are invalid.
        """
        user = self.repo.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            logger.warning("Failed login attempt for email: %s", payload.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
        logger.info("User logged in: %s", user.email)
        return user, token
