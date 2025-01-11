import pytest
from backend.queries import get_notes_with_cache, get_note_detail_with_cache


@pytest.mark.skip(reason="Requires database connection")
def test_notes_query(db, schema):
    """Test notes query with caching"""
    # Test without filters
    notes = get_notes_with_cache(schema)
    assert isinstance(notes, list)

    # Test with filters
    filtered = get_notes_with_cache(
        schema, {"keyword": "test", "start_date": "2024-01-01"}
    )
    assert isinstance(filtered, list)


@pytest.mark.skip(reason="Requires database connection")
def test_note_detail_query(db, schema):
    """Test note detail query with caching"""
    # Test with valid audio key
    note = get_note_detail_with_cache(schema, "test_123")
    assert note is None or isinstance(note, tuple)
