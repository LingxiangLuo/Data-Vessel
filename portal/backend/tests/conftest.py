"""pytest fixtures: SQLite in-memory DB + dependency overrides"""
import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)

# Patch the module-level engine before any app code imports it
import app.core.database as _db_module
_db_module.engine = _test_engine
_db_module.SessionLocal = sessionmaker(bind=_test_engine)

from app.core.database import Base

Base.metadata.create_all(bind=_test_engine)


@pytest.fixture
def db_session():
    Session = sessionmaker(bind=_test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
