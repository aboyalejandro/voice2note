import pytest
from backend.database import DatabaseManager
from backend.cache import QueryCache
from backend.config import db_config
import os


@pytest.fixture
def db():
    """Database manager fixture"""
    return DatabaseManager(db_config)


@pytest.fixture
def cache():
    """Cache fixture"""
    return QueryCache(redis_url=os.getenv("REDIS_URL"))


@pytest.fixture
def schema():
    """Test schema fixture"""
    return "user_999"  # Use a test schema
