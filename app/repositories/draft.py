"""
NAYAM (नयम्) — Draft Repository.

Database operations for the Draft model.
"""

import logging
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.draft import Draft, DraftType, DraftStatus

logger = logging.getLogger(__name__)


class DraftRepository:
    """Repository for Draft CRUD operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, draft_id: UUID) -> Optional[Draft]:
        return self.db.query(Draft).filter(Draft.id == draft_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        draft_type: Optional[DraftType] = None,
        status: Optional[DraftStatus] = None,
        department: Optional[str] = None,
    ) -> Tuple[List[Draft], int]:
        query = self.db.query(Draft)

        if draft_type:
            query = query.filter(Draft.draft_type == draft_type)
        if status:
            query = query.filter(Draft.status == status)
        if department:
            query = query.filter(Draft.department == department)

        total = query.count()
        drafts = query.order_by(Draft.created_at.desc()).offset(skip).limit(limit).all()
        return drafts, total

    def create(self, draft: Draft) -> Draft:
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)
        logger.info("Created draft: %s — %s", draft.id, draft.title)
        return draft

    def update(self, draft: Draft) -> Draft:
        self.db.commit()
        self.db.refresh(draft)
        logger.info("Updated draft: %s", draft.id)
        return draft

    def delete(self, draft: Draft) -> None:
        self.db.delete(draft)
        self.db.commit()
        logger.info("Deleted draft: %s", draft.id)

    def total_count(self) -> int:
        return self.db.query(Draft).count()
