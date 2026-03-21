"""
Jenan BIZ — Database Setup (async SQLAlchemy)
"""

import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from app.config import get_settings

settings = get_settings()

# Build engine kwargs — SQLite doesn't support pool_size/max_overflow
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
_engine_kwargs: dict = {
    "echo": settings.DEBUG,
}
if not _is_sqlite:
    _ssl_ctx = ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl.CERT_NONE
    _engine_kwargs.update(
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        connect_args={"ssl": _ssl_ctx, "statement_cache_size": 0},
    )

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

# SQLite: enable WAL mode + foreign keys
if _is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Dependency: yields an async DB session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all tables (for development). Use Alembic in production."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Apply incremental column additions that create_all won't handle
    await _run_schema_migrations()


async def _run_schema_migrations():
    """
    Run lightweight ADD COLUMN IF NOT EXISTS migrations for production.
    Safe to run on every startup — idempotent.
    """
    from sqlalchemy import text
    is_sqlite = settings.DATABASE_URL.startswith("sqlite")

    migrations = []

    if is_sqlite:
        # SQLite: check if column exists first (no IF NOT EXISTS support in older versions)
        migrations = [
            ("cases", "completion_required_docs", "TEXT", None),
        ]
        async with engine.begin() as conn:
            for table, column, col_type, default in migrations:
                result = await conn.execute(text(f"PRAGMA table_info({table})"))
                existing = [row[1] for row in result.fetchall()]
                if column not in existing:
                    await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
    else:
        # PostgreSQL: use IF NOT EXISTS
        migrations = [
            "ALTER TABLE cases ADD COLUMN IF NOT EXISTS completion_required_docs JSONB",
        ]
        async with engine.begin() as conn:
            for stmt in migrations:
                await conn.execute(text(stmt))
