"""
NAYAM (नयम्) — Privacy Models (Phase 3).

Encryption metadata tracking for the Zero-Knowledge Privacy Layer.
Stores per-field encryption records so the system knows which
citizen data is encrypted and can enforce role-based decryption gates.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Enum, Index, String, Text, Uuid,
)

from app.core.database import Base


class EncryptionAlgorithm(str, enum.Enum):
    """Supported encryption algorithms."""
    AES_256_GCM = "aes-256-gcm"
    FERNET = "fernet"


class EncryptedFieldRegistry(Base):
    """
    Registry of encrypted PII fields.

    Tracks which fields of which entities are currently encrypted
    and the key references needed for authorised decryption.

    Attributes:
        id:             UUID primary key.
        entity_type:    Source table (e.g. "citizen").
        entity_id:      UUID of the encrypted entity.
        field_name:     Column name that holds ciphertext.
        algorithm:      Encryption algorithm used.
        key_reference:  Opaque key identifier (NOT the key itself).
        encrypted_at:   When the field was encrypted.
    """

    __tablename__ = "encrypted_field_registry"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Uuid, nullable=False)
    field_name = Column(String(100), nullable=False)
    algorithm = Column(
        Enum(EncryptionAlgorithm, name="encryption_algo_enum", native_enum=False),
        nullable=False,
        default=EncryptionAlgorithm.FERNET,
    )
    key_reference = Column(String(255), nullable=False)
    encrypted_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_enc_registry_entity", "entity_type", "entity_id"),
        Index("ix_enc_registry_field", "field_name"),
        Index("ix_enc_registry_encrypted_at", "encrypted_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<EncryptedFieldRegistry(entity={self.entity_type}:{self.entity_id}, "
            f"field={self.field_name}, algo={self.algorithm})>"
        )
