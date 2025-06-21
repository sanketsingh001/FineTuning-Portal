from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a scoped session factory
ScopedSession = scoped_session(SessionLocal)

# Base class for models
Base = declarative_base()

def get_db():
    ""
    Dependency function to get DB session.
    Use this in FastAPI path operations to get a DB session.
    """
    db = ScopedSession()
    try:
        yield db
    finally:
        db.close()
