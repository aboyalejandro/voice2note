import pytest
from backend.database import DatabaseManager


def test_schema_validation(db):
    """Test schema validation"""
    # Valid schema
    assert db.validate_schema("user_123") == "user_123"

    # Invalid schemas
    assert db.validate_schema(None) is None
    assert db.validate_schema("invalid") is None
    assert db.validate_schema("user_abc") is None


def test_schema_id_extraction(db):
    """Test schema ID extraction"""
    assert db.get_schema_id("user_123") == 123
    assert db.get_schema_id("invalid") is None
    assert db.get_schema_id(None) is None


@pytest.mark.skip(reason="Requires database connection")
def test_connection_pool(db):
    """Test database connection pooling"""
    with db.get_connection() as conn:
        assert conn is not None
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1
