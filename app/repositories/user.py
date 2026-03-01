"""
NAYAM (नयम्) — User Repository.

Handles all database operations for the User model.
No business logic — only data access.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    """
    Repository for User CRUD operations.

    Args:
        db: SQLAlchemy database session.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: str | UUID) -> Optional[User]:
        """
        Retrieve a user by their UUID.

        Args:
            user_id: The UUID of the user.

        Returns:
            User object or None if not found.
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.

        Args:
            email: The email to look up.

        Returns:
            User object or None if not found.
        """
        return self.db.query(User).filter(User.email == email).first()

    def create(self, user: User) -> User:
        """
        Persist a new user to the database.

        Args:
            user: The User ORM instance to persist.

        Returns:
            The persisted User object with generated ID.
        """
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        logger.info("Created user: %s (%s)", user.email, user.role)
        return user

    def email_exists(self, email: str) -> bool:
        """
        Check if an email is already registered.

        Args:
            email: The email to check.

        Returns:
            True if the email exists, False otherwise.
        """
        return self.db.query(User).filter(User.email == email).count() > 0
