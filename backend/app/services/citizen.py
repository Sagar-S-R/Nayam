"""
NAYAM (नयम्) — Citizen Service.

Business logic for citizen management.
Delegates data access to CitizenRepository.
"""

import logging
from typing import List, Tuple, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.citizen import Citizen
from app.repositories.citizen import CitizenRepository
from app.schemas.citizen import CitizenCreateRequest, CitizenUpdateRequest

logger = logging.getLogger(__name__)


class CitizenService:
    """
    Service layer for citizen operations.

    Args:
        db: SQLAlchemy database session.
    """

    def __init__(self, db: Session) -> None:
        self.repo = CitizenRepository(db)

    def create_citizen(self, payload: CitizenCreateRequest) -> Citizen:
        """
        Create a new citizen record.

        Args:
            payload: Citizen creation data.

        Returns:
            The created Citizen object.
        """
        citizen = Citizen(
            name=payload.name,
            contact_number=payload.contact_number,
            ward=payload.ward,
        )
        return self.repo.create(citizen)

    def get_citizen(self, citizen_id: UUID) -> Citizen:
        """
        Retrieve a single citizen by ID.

        Args:
            citizen_id: UUID of the citizen.

        Returns:
            The Citizen object.

        Raises:
            HTTPException: 404 if citizen not found.
        """
        citizen = self.repo.get_by_id(citizen_id)
        if citizen is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Citizen with id {citizen_id} not found.",
            )
        return citizen

    def list_citizens(
        self,
        skip: int = 0,
        limit: int = 50,
        ward: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Citizen], int]:
        """
        List citizens with optional filtering and pagination.

        Args:
            skip: Records to skip.
            limit: Max records to return.
            ward: Optional ward filter.
            search: Optional name search.

        Returns:
            Tuple of (list of citizens, total count).
        """
        return self.repo.get_all(skip=skip, limit=limit, ward=ward, search=search)

    def update_citizen(self, citizen_id: UUID, payload: CitizenUpdateRequest) -> Citizen:
        """
        Update an existing citizen's details.

        Args:
            citizen_id: UUID of the citizen to update.
            payload: Fields to update (partial update supported).

        Returns:
            The updated Citizen object.

        Raises:
            HTTPException: 404 if citizen not found.
        """
        citizen = self.get_citizen(citizen_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(citizen, field, value)

        return self.repo.update(citizen)

    def delete_citizen(self, citizen_id: UUID) -> None:
        """
        Delete a citizen record.

        Args:
            citizen_id: UUID of the citizen to delete.

        Raises:
            HTTPException: 404 if citizen not found.
        """
        citizen = self.get_citizen(citizen_id)
        self.repo.delete(citizen)
        logger.info("Citizen deleted: %s", citizen_id)
