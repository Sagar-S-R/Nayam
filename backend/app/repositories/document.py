"""
NAYAM (नयम्) — Document Repository.

Handles all database operations for the Document model.
"""

import logging
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import Document

logger = logging.getLogger(__name__)


class DocumentRepository:
    """
    Repository for Document CRUD operations.

    Args:
        db: SQLAlchemy database session.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, doc_id: UUID) -> Optional[Document]:
        """
        Retrieve a document by its UUID.

        Args:
            doc_id: The UUID of the document.

        Returns:
            Document object or None.
        """
        return self.db.query(Document).filter(Document.id == doc_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Document], int]:
        """
        Retrieve a paginated list of documents.

        Args:
            skip: Records to skip.
            limit: Max records to return.

        Returns:
            Tuple of (list of documents, total count).
        """
        query = self.db.query(Document)
        total = query.count()
        documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
        return documents, total

    def get_recent(self, limit: int = 5) -> List[Document]:
        """
        Get the most recent documents.

        Args:
            limit: Number of recent documents to return.

        Returns:
            List of recent Document objects.
        """
        return (
            self.db.query(Document)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .all()
        )

    def create(self, document: Document) -> Document:
        """
        Persist a new document record.

        Args:
            document: The Document ORM instance.

        Returns:
            The persisted Document with generated ID.
        """
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        logger.info("Created document: %s", document.title)
        return document

    def update(self, document: Document) -> Document:
        """
        Update an existing document record.

        Args:
            document: The modified Document ORM instance.

        Returns:
            The updated Document object.
        """
        self.db.commit()
        self.db.refresh(document)
        logger.info("Updated document: %s", document.id)
        return document

    def delete(self, document: Document) -> None:
        """
        Delete a document record.

        Args:
            document: The Document ORM instance to delete.
        """
        self.db.delete(document)
        self.db.commit()
        logger.info("Deleted document: %s", document.id)

    def total_count(self) -> int:
        """
        Get total number of documents.

        Returns:
            Integer count of all documents.
        """
        return self.db.query(Document).count()
