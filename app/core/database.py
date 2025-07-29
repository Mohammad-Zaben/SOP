"""
PostgreSQL database connection setup using SQLModel
Contains database engine, session management, and connection utilities
"""
from typing import Generator
from sqlmodel import Session, create_engine
from sqlalchemy.orm import sessionmaker

from .config import get_settings

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,   # Verify connections before use
    pool_recycle=300,     # Recycle connections every 5 minutes
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session
)


def get_session() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI routes.
    
    Yields:
        Session: SQLModel database session
        
    Usage:
        @app.get("/")
        def read_items(session: Session = Depends(get_session)):
            # Use session here
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_db_and_tables() -> None:
    """
    Create database tables based on SQLModel definitions.
    This should be called during application startup.
    """
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
