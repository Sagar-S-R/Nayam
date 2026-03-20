"""
NAYAM — Direct database initialization from ORM models.
Use this to create all tables from SQLAlchemy models.
"""

from app.core.database import engine
from app.models import Base

if __name__ == "__main__":
    print("Creating all tables from ORM models...")
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully!")
