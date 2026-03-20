"""
NAYAM (नयम्) — Citizen Repository.

Handles all database operations for the Citizen model.
"""

import logging
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.citizen import Citizen

logger = logging.getLogger(__name__)


class CitizenRepository:
    """
    Repository for Citizen CRUD operations.

    Args:
        db: SQLAlchemy database session.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, citizen_id: UUID) -> Optional[Citizen]:
        """
        Retrieve a citizen by their UUID.

        Args:
            citizen_id: The UUID of the citizen.

        Returns:
            Citizen object or None.
        """
        return self.db.query(Citizen).filter(Citizen.id == citizen_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        ward: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Citizen], int]:
        """
        Retrieve a paginated list of citizens with optional filters.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            ward: Optional ward filter.
            search: Optional name search string.

        Returns:
            Tuple of (list of citizens, total count).
        """
        query = self.db.query(Citizen)

        if ward:
            query = query.filter(Citizen.ward == ward)
        if search:
            query = query.filter(Citizen.name.ilike(f"%{search}%"))

        total = query.count()
        citizens = query.order_by(Citizen.created_at.desc()).offset(skip).limit(limit).all()
        return citizens, total

    def create(self, citizen: Citizen) -> Citizen:
        """
        Persist a new citizen record.

        Args:
            citizen: The Citizen ORM instance.

        Returns:
            The persisted Citizen with generated ID.
        """
        self.db.add(citizen)
        self.db.commit()
        self.db.refresh(citizen)
        logger.info("Created citizen: %s (ward: %s)", citizen.name, citizen.ward)
        return citizen

    def update(self, citizen: Citizen) -> Citizen:
        """
        Update an existing citizen record.

        Args:
            citizen: The modified Citizen ORM instance.

        Returns:
            The updated Citizen object.
        """
        self.db.commit()
        self.db.refresh(citizen)
        logger.info("Updated citizen: %s", citizen.id)
        return citizen

    def delete(self, citizen: Citizen) -> None:
        """
        Delete a citizen record.

        Args:
            citizen: The Citizen ORM instance to delete.
        """
        self.db.delete(citizen)
        self.db.commit()
        logger.info("Deleted citizen: %s", citizen.id)
