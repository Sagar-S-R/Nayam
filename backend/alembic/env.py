"""
NAYAM (नयम्) — Alembic Environment Configuration.

Configures Alembic to use the application's SQLAlchemy models
and database connection for migrations.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from app.core.config import get_settings
from app.core.database import Base

# Import all models so Alembic can detect them
from app.models import (  # noqa: F401
    User, Citizen, Issue, Document,                       # Phase 1
    Conversation, Embedding, ActionRequest,               # Phase 2
    RiskScore, AnomalyLog, GeoCluster,                    # Phase 3
    TaskRecommendation, ExecutionFeedback,                 # Phase 3
    AuditLog, EncryptedFieldRegistry,                     # Phase 3
    SyncQueue, ConflictLog, OfflineAction,                # Phase 4
    ComplianceExport, PerformanceMetric, RateLimitRecord,  # Phase 4
)

# Alembic Config object
config = context.config

# Override sqlalchemy.url from environment
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Logging configuration
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
